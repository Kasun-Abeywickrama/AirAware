"""Run the packaged AirAware operational models against validated live inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import torch
from torch import nn

from ..config import Settings
from ..models.pm25_observation import Pm25Observation
from ..models.weather_record import WeatherRecord


LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")


class ForecastGenerationError(RuntimeError):
    """A safe failure when forecast inputs or local artifacts are unavailable."""


class GRURegressor(nn.Module):
    """Architecture matching the already trained AirAware GRU artifacts."""

    def __init__(self, features: int, hidden: int = 32) -> None:
        super().__init__()
        self.gru = nn.GRU(features, hidden, batch_first=True)
        self.output = nn.Linear(hidden, 1)

    def forward(self, inputs):
        values, _ = self.gru(inputs)
        return self.output(values[:, -1]).squeeze(-1)


@dataclass(frozen=True)
class GeneratedForecast:
    horizon_hours: int
    target_at: datetime
    predicted_value_ug_m3: Decimal
    lower_bound_ug_m3: Decimal
    upper_bound_ug_m3: Decimal
    explanation: "GeneratedExplanation"


@dataclass(frozen=True)
class GeneratedExplanation:
    """A validated, grouped local explanation in PM2.5 units."""

    method: str
    baseline_value_ug_m3: Decimal
    completeness_error_ug_m3: Decimal
    factors: list[dict[str, Any]]


FACTOR_DEFINITIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("current_pm25", "Current air quality", ("pm25_lag_0",)),
    ("recent_pm25", "Recent PM2.5 trend", ("pm25_lag_1", "pm25_lag_2", "pm25_lag_3", "pm25_lag_6")),
    ("older_pm25", "Earlier PM2.5 pattern", ("pm25_lag_12", "pm25_lag_24", "pm25_lag_48", "pm25_lag_72", "pm25_lag_168")),
    ("temperature_moisture", "Temperature and moisture", ("temperature_2m", "relative_humidity_2m", "dew_point_2m")),
    ("rainfall", "Rainfall", ("precipitation",)),
    ("solar_radiation", "Sunlight", ("shortwave_radiation",)),
    ("air_pressure", "Air pressure", ("surface_pressure",)),
    ("wind_speed", "Wind speed", ("wind_speed_10m",)),
    ("wind_direction", "Wind direction", ("wind_direction_sin", "wind_direction_cos")),
    ("time_of_day", "Time of day", ("hour_sin", "hour_cos")),
    # This operational model does not use a day-of-week input. It stays visible
    # so the interface honestly distinguishes an unused factor from a low effect.
    ("day_of_week", "Day-of-week pattern", ()),
    ("seasonal_pattern", "Seasonal pattern", ("doy_sin", "doy_cos")),
)
FACTOR_BY_FEATURE = {
    feature: key for key, _label, features in FACTOR_DEFINITIONS for feature in features
}


class PackagedModelService:
    """Load verified local artifacts and produce the three supported horizons."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._manifest = self._load_manifest()

    @property
    def model_version(self) -> str:
        return str(self._manifest["model_version"])

    def generate(
        self,
        *,
        pm25_records: list[Pm25Observation],
        weather_records: list[WeatherRecord],
        issue_at: datetime,
    ) -> tuple[list[GeneratedForecast], str]:
        """Generate exact-model outputs after readiness checks have passed."""
        self._verify_artifacts()
        frame = _build_feature_frame(pm25_records, weather_records, issue_at, self._manifest)
        tree_features = _tree_feature_names(self._manifest)
        row = np.asarray([[frame[-1][name] for name in tree_features]], dtype=np.float32)
        sequence_names = list(self._manifest["base_features"])
        sequence = np.asarray(
            [[entry[name] for name in sequence_names] for entry in frame[-24:]],
            dtype=np.float32,
        )
        if not np.isfinite(row).all() or not np.isfinite(sequence).all():
            raise ForecastGenerationError("Forecast input values are incomplete.")

        forecasts: list[GeneratedForecast] = []
        for raw_horizon, specification in self._manifest["horizons"].items():
            horizon = int(raw_horizon)
            try:
                tree = joblib.load(self._artifact_path(specification["tree_artifact"]))
                tree_prediction = float(tree.predict(row)[0])
                if specification["model_family"] == "XGBoost-GRU":
                    gru_prediction = self._predict_gru(specification["gru_artifact"], sequence)
                    weight = float(specification["xgboost_weight"])
                    prediction = weight * tree_prediction + (1 - weight) * gru_prediction
                else:
                    prediction = tree_prediction
            except (ForecastGenerationError, OSError, RuntimeError, ValueError, KeyError) as error:
                raise ForecastGenerationError("Required forecast model files are unavailable.") from error

            prediction = max(0.0, prediction)
            offset = float(specification["conformal_offset"])
            explanation = self._build_explanation(
                tree=tree,
                row=row,
                tree_feature_names=tree_features,
                specification=specification,
                sequence=sequence,
                prediction=prediction,
            )
            forecasts.append(
                GeneratedForecast(
                    horizon_hours=horizon,
                    target_at=issue_at + timedelta(hours=horizon),
                    predicted_value_ug_m3=_decimal(prediction),
                    lower_bound_ug_m3=_decimal(max(0.0, prediction - offset)),
                    upper_bound_ug_m3=_decimal(prediction + offset),
                    explanation=explanation,
                )
            )

        input_version = hashlib.sha256(
            np.asarray(
                [[entry[name] for name in tree_features] for entry in frame], dtype=np.float32
            ).tobytes()
        ).hexdigest()
        return sorted(forecasts, key=lambda item: item.horizon_hours), input_version

    def _load_manifest(self) -> dict[str, Any]:
        path = Path(__file__).resolve().parents[2] / "model_manifest.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ForecastGenerationError("Forecast model manifest is unavailable.") from error

    def _artifact_path(self, filename: str) -> Path:
        return self._settings.model_artifact_directory / filename

    def _verify_artifacts(self) -> None:
        for filename, expected_hash in self._manifest["artifact_hashes"].items():
            path = self._artifact_path(filename)
            try:
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                actual_hash = digest.hexdigest()
            except OSError as error:
                raise ForecastGenerationError("Required forecast model files are unavailable.") from error
            if actual_hash != expected_hash:
                raise ForecastGenerationError("Forecast model file verification failed.")

    def _predict_gru(self, filename: str, sequence: np.ndarray) -> float:
        model, payload, scaled = self._load_gru(filename, sequence)
        with torch.no_grad():
            value = model(torch.tensor(scaled[None, :, :], dtype=torch.float32)).item()
        return float(value * payload["target_scale"] + payload["target_mean"])

    def _load_gru(self, filename: str, sequence: np.ndarray) -> tuple[GRURegressor, dict[str, Any], np.ndarray]:
        try:
            payload = torch.load(self._artifact_path(filename), map_location="cpu", weights_only=False)
            model = GRURegressor(len(payload["features"]))
            model.load_state_dict(payload["state_dict"])
        except (OSError, KeyError, RuntimeError, ValueError) as error:
            raise ForecastGenerationError("Required forecast model files are unavailable.") from error
        model.eval()
        scaled = (sequence - np.asarray(payload["scaler_mean"])) / np.asarray(payload["scaler_scale"])
        return model, payload, scaled

    def _build_explanation(
        self,
        *,
        tree: Any,
        row: np.ndarray,
        tree_feature_names: list[str],
        specification: dict[str, Any],
        sequence: np.ndarray,
        prediction: float,
    ) -> GeneratedExplanation:
        """Explain the exact saved model output, then verify its reconstruction."""
        tree_base, tree_values = _tree_shap_values(tree, row)
        grouped_tree = _group_contributions(tree_feature_names, tree_values)
        if specification["model_family"] == "XGBoost-GRU":
            gru_base, gru_values = self._gru_integrated_gradients(
                specification["gru_artifact"], sequence
            )
            grouped_gru = _group_sequence_contributions(
                list(self._manifest["base_features"]), gru_values
            )
            weight = float(specification["xgboost_weight"])
            baseline = weight * tree_base + (1 - weight) * gru_base
            grouped = {
                key: weight * grouped_tree[key] + (1 - weight) * grouped_gru[key]
                for key, _label, _features in FACTOR_DEFINITIONS
            }
            method = "TreeSHAP + Integrated Gradients"
        else:
            baseline = tree_base
            grouped = grouped_tree
            method = "TreeSHAP"

        reconstructed = baseline + sum(grouped.values())
        error = abs(prediction - reconstructed)
        # The local explanation must reconstruct the operational prediction.
        # A larger discrepancy usually means the artifact or explainer is incompatible.
        if error > 0.25:
            raise ForecastGenerationError("Forecast explanation validation failed.")
        return GeneratedExplanation(
            method=method,
            baseline_value_ug_m3=_decimal(baseline),
            completeness_error_ug_m3=_decimal(error),
            factors=_rank_factors(grouped),
        )

    def _gru_integrated_gradients(
        self, filename: str, sequence: np.ndarray, steps: int = 256
    ) -> tuple[float, np.ndarray]:
        """Return a GRU baseline and Integrated Gradients in PM2.5 units."""
        model, payload, scaled = self._load_gru(filename, sequence)
        inputs = torch.tensor(scaled, dtype=torch.float32)
        baseline = torch.zeros_like(inputs)
        total_gradients = torch.zeros_like(inputs)
        for alpha in torch.linspace(1 / steps, 1, steps):
            sample = (baseline + alpha * (inputs - baseline)).unsqueeze(0).detach().requires_grad_(True)
            model(sample).sum().backward()
            total_gradients += sample.grad.squeeze(0)
            model.zero_grad(set_to_none=True)
        target_scale = float(payload["target_scale"])
        contributions = ((inputs - baseline) * (total_gradients / steps)).detach().numpy() * target_scale
        with torch.no_grad():
            baseline_value = model(baseline.unsqueeze(0)).item()
        return float(baseline_value * target_scale + payload["target_mean"]), contributions


def _build_feature_frame(
    pm25_records: list[Pm25Observation],
    weather_records: list[WeatherRecord],
    issue_at: datetime,
    manifest: dict[str, Any],
) -> list[dict[str, float]]:
    issue_local = issue_at.astimezone(LOCAL_TIMEZONE).replace(minute=0, second=0, microsecond=0)
    hours = [issue_local - timedelta(hours=offset) for offset in reversed(range(169))]
    pm25_by_hour: dict[datetime, list[float]] = {}
    for record in pm25_records:
        hour = record.observed_at.astimezone(LOCAL_TIMEZONE).replace(minute=0, second=0, microsecond=0)
        pm25_by_hour.setdefault(hour, []).append(float(record.value_ug_m3))
    weather_by_hour = {
        record.valid_at.astimezone(LOCAL_TIMEZONE).replace(minute=0, second=0, microsecond=0): record
        for record in weather_records
    }

    values: list[dict[str, float]] = []
    for hour in hours:
        pm25_values = pm25_by_hour.get(hour)
        weather = weather_by_hour.get(hour)
        if not pm25_values:
            raise ForecastGenerationError("Required forecast input history is incomplete.")
        # The tree uses the issue-hour weather features and the GRU uses only
        # the final 24 hourly rows. Older weather values are never consumed by
        # either packaged model, so they may be absent from a fresh deployment.
        if weather is None:
            weather_features = {
                "temperature_2m": float("nan"),
                "relative_humidity_2m": float("nan"),
                "dew_point_2m": float("nan"),
                "surface_pressure": float("nan"),
                "precipitation": float("nan"),
                "shortwave_radiation": float("nan"),
                "wind_speed_10m": float("nan"),
                "wind_direction_sin": float("nan"),
                "wind_direction_cos": float("nan"),
            }
        else:
            weather_values = (
                weather.temperature_c,
                weather.humidity_percent,
                weather.dew_point_c,
                weather.surface_pressure_hpa,
                weather.precipitation_mm,
                weather.shortwave_radiation_w_m2,
                weather.wind_speed_kmh,
                weather.wind_direction_degrees,
            )
            if any(value is None for value in weather_values):
                raise ForecastGenerationError("Required forecast weather history is incomplete.")
            direction = np.deg2rad(float(weather.wind_direction_degrees))
            weather_features = {
                "temperature_2m": float(weather.temperature_c),
                "relative_humidity_2m": float(weather.humidity_percent),
                "dew_point_2m": float(weather.dew_point_c),
                "surface_pressure": float(weather.surface_pressure_hpa),
                "precipitation": float(weather.precipitation_mm),
                "shortwave_radiation": float(weather.shortwave_radiation_w_m2),
                "wind_speed_10m": float(weather.wind_speed_kmh),
                "wind_direction_sin": float(np.sin(direction)),
                "wind_direction_cos": float(np.cos(direction)),
            }
        values.append(
            {
                "pm25": float(np.mean(pm25_values)),
                **weather_features,
                "hour_sin": float(np.sin(2 * np.pi * hour.hour / 24)),
                "hour_cos": float(np.cos(2 * np.pi * hour.hour / 24)),
                "doy_sin": float(np.sin(2 * np.pi * hour.timetuple().tm_yday / 365.25)),
                "doy_cos": float(np.cos(2 * np.pi * hour.timetuple().tm_yday / 365.25)),
            }
        )
    for index, item in enumerate(values):
        for lag in manifest["pm25_lags"]:
            item[f"pm25_lag_{lag}"] = values[index - lag]["pm25"] if index >= lag else float("nan")
    return values


def _tree_feature_names(manifest: dict[str, Any]) -> list[str]:
    return [f"pm25_lag_{lag}" for lag in manifest["pm25_lags"]] + [
        name for name in manifest["base_features"] if name != "pm25"
    ]


def _tree_shap_values(tree: Any, row: np.ndarray) -> tuple[float, np.ndarray]:
    """Calculate exact TreeSHAP values for an XGBoost or sklearn tree artifact."""
    try:
        import shap

        explainer = shap.TreeExplainer(tree)
        values = np.asarray(explainer.shap_values(row), dtype=float)
        expected = np.asarray(explainer.expected_value, dtype=float).reshape(-1)
    except (ImportError, AttributeError, RuntimeError, TypeError, ValueError) as error:
        raise ForecastGenerationError("Forecast explanation is unavailable for this model.") from error
    if values.ndim == 3:
        values = values[:, :, 0]
    if values.ndim != 2 or values.shape[0] != 1:
        raise ForecastGenerationError("Forecast explanation is unavailable for this model.")
    return float(expected[0]), values[0]


def _empty_groups() -> dict[str, float]:
    return {key: 0.0 for key, _label, _features in FACTOR_DEFINITIONS}


def _group_contributions(feature_names: list[str], values: np.ndarray) -> dict[str, float]:
    """Aggregate model-level features into the public 12-factor vocabulary."""
    grouped = _empty_groups()
    for name, value in zip(feature_names, values, strict=True):
        factor = FACTOR_BY_FEATURE.get(name)
        if factor is not None:
            grouped[factor] += float(value)
    return grouped


def _group_sequence_contributions(feature_names: list[str], values: np.ndarray) -> dict[str, float]:
    """Aggregate a 24-hour GRU attribution tensor into the same factors."""
    grouped = _empty_groups()
    for index, name in enumerate(feature_names):
        if name == "pm25":
            # The sequence runs from oldest to newest. Preserve the meaning of
            # the public PM2.5 groups instead of calling every past value
            # "current" merely because the GRU stores it in one input column.
            for step, value in enumerate(values[:, index]):
                lag_hours = len(values) - 1 - step
                factor = "current_pm25" if lag_hours == 0 else "recent_pm25" if lag_hours <= 6 else "older_pm25"
                grouped[factor] += float(value)
            continue
        factor = FACTOR_BY_FEATURE.get(name)
        if factor is not None:
            grouped[factor] += float(values[:, index].sum())
    return grouped


def _rank_factors(grouped: dict[str, float]) -> list[dict[str, Any]]:
    """Produce UI-safe values: top three first, all twelve always present."""
    supported = [key for key, _label, features in FACTOR_DEFINITIONS if features]
    ranking = sorted(supported, key=lambda key: abs(grouped[key]), reverse=True)
    rank_by_key = {key: index + 1 for index, key in enumerate(ranking)}
    total = sum(abs(grouped[key]) for key in supported)
    items: list[dict[str, Any]] = []
    for key, label, features in FACTOR_DEFINITIONS:
        contribution = grouped[key]
        used = bool(features)
        items.append(
            {
                "key": key,
                "label": label,
                "contribution_ug_m3": float(_decimal(contribution)),
                "direction": "increased" if contribution > 0.005 else "decreased" if contribution < -0.005 else "neutral",
                "absolute_share_percent": float(_decimal(100 * abs(contribution) / total)) if total else 0.0,
                "rank": rank_by_key.get(key),
                "is_top_3": rank_by_key.get(key, 99) <= 3,
                "used_by_model": used,
            }
        )
    return sorted(items, key=lambda item: (not item["is_top_3"], item["rank"] or 99, item["label"]))


def _decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
