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
            forecasts.append(
                GeneratedForecast(
                    horizon_hours=horizon,
                    target_at=issue_at + timedelta(hours=horizon),
                    predicted_value_ug_m3=_decimal(prediction),
                    lower_bound_ug_m3=_decimal(max(0.0, prediction - offset)),
                    upper_bound_ug_m3=_decimal(prediction + offset),
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
        try:
            payload = torch.load(self._artifact_path(filename), map_location="cpu", weights_only=False)
            model = GRURegressor(len(payload["features"]))
            model.load_state_dict(payload["state_dict"])
        except (OSError, KeyError, RuntimeError, ValueError) as error:
            raise ForecastGenerationError("Required forecast model files are unavailable.") from error
        model.eval()
        scaled = (sequence - np.asarray(payload["scaler_mean"])) / np.asarray(payload["scaler_scale"])
        with torch.no_grad():
            value = model(torch.tensor(scaled[None, :, :], dtype=torch.float32)).item()
        return float(value * payload["target_scale"] + payload["target_mean"])


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
        if not pm25_values or weather is None:
            raise ForecastGenerationError("Required forecast input history is incomplete.")
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
        values.append(
            {
                "pm25": float(np.mean(pm25_values)),
                "temperature_2m": float(weather.temperature_c),
                "relative_humidity_2m": float(weather.humidity_percent),
                "dew_point_2m": float(weather.dew_point_c),
                "surface_pressure": float(weather.surface_pressure_hpa),
                "precipitation": float(weather.precipitation_mm),
                "shortwave_radiation": float(weather.shortwave_radiation_w_m2),
                "wind_speed_10m": float(weather.wind_speed_kmh),
                "wind_direction_sin": float(np.sin(direction)),
                "wind_direction_cos": float(np.cos(direction)),
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


def _decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
