"""
Service: Machine Learning Forecasting and Explainability Engine.

This is the core ML execution engine for AirAware. It performs:
1. Model Artifact Verification: Checks SHA-256 integrity hashes of PyTorch & XGBoost model files.
2. Feature Matrix Engineering: Generates 168-hour PM2.5 lags, cyclical temporal encodings (hour/day of year sin/cos),
   and wind direction trigonometric vectors.
3. Multi-Horizon Inference:
   - 1-Hour Horizon: Fast tree-based point forecast.
   - 6-Hour & 24-Hour Horizons: Hybrid Ensemble combining XGBoost and PyTorch GRU Recurrent Neural Networks.
4. Conformal Prediction: Applies distribution-free prediction intervals (calibrated offsets) to output
   statistically guaranteed lower and upper uncertainty bounds.
5. Explainable AI (XAI):
   - TreeSHAP for tree-based models.
   - Integrated Gradients for PyTorch GRU sequence models.
   - Aggregates attributions into 12 human-understandable factor categories (e.g., current air quality, wind speed, sunlight).
"""

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


# Station reference timezone for calendar and diurnal feature calculations
LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")


class ForecastGenerationError(RuntimeError):
    """Exception raised when forecast inference fails safely due to missing artifacts or invalid inputs."""


class GRURegressor(nn.Module):
    """
    PyTorch Gated Recurrent Unit (GRU) neural network architecture.
    
    Processes sequential 24-hour meteorological and PM2.5 time series to capture temporal dependencies.
    """

    def __init__(self, features: int, hidden: int = 32) -> None:
        """
        Initialize GRU layers.

        Args:
            features: Number of input features per time step.
            hidden: Number of hidden units in the GRU cell (default: 32).
        """
        super().__init__()
        self.gru = nn.GRU(features, hidden, batch_first=True)
        self.output = nn.Linear(hidden, 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GRU and final linear regressor head.

        Args:
            inputs: Tensor of shape (batch_size, sequence_length, features).

        Returns:
            Scalar PM2.5 prediction tensor of shape (batch_size,).
        """
        values, _ = self.gru(inputs)
        return self.output(values[:, -1]).squeeze(-1)


@dataclass(frozen=True)
class GeneratedForecast:
    """Container holding single-horizon forecast prediction and its calibrated uncertainty bounds."""

    horizon_hours: int
    target_at: datetime
    predicted_value_ug_m3: Decimal
    lower_bound_ug_m3: Decimal
    upper_bound_ug_m3: Decimal
    explanation: "GeneratedExplanation"


@dataclass(frozen=True)
class GeneratedExplanation:
    """Container holding XAI feature importance attributions in physical PM2.5 units (ug/m3)."""

    method: str
    baseline_value_ug_m3: Decimal
    completeness_error_ug_m3: Decimal
    factors: list[dict[str, Any]]


# Standardized 12-factor ontology mapping raw model input features to human-friendly categories
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
    # This operational model does not use day-of-week input, kept visible for transparency in UI
    ("day_of_week", "Day-of-week pattern", ()),
    ("seasonal_pattern", "Seasonal pattern", ("doy_sin", "doy_cos")),
)

FACTOR_BY_FEATURE = {
    feature: key for key, _label, features in FACTOR_DEFINITIONS for feature in features
}


class PackagedModelService:
    """Service to load ML model artifacts, execute multi-horizon predictions, and generate XAI explanations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize service with configuration settings and load model manifest."""
        self._settings = settings
        self._manifest = self._load_manifest()

    @property
    def model_version(self) -> str:
        """Return the active model release version string from the manifest."""
        return str(self._manifest["model_version"])

    def generate(
        self,
        *,
        pm25_records: list[Pm25Observation],
        weather_records: list[WeatherRecord],
        issue_at: datetime,
    ) -> tuple[list[GeneratedForecast], str]:
        """
        Execute operational inference across all 3 horizons (1h, 6h, 24h).

        Workflow:
        1. Verify model file SHA-256 checksums to ensure artifacts are untampered.
        2. Construct feature matrix (168-hour lags, cyclical time, weather variables).
        3. Run model inference (Tree models & GRU models, applying ensemble weights).
        4. Apply conformal prediction offsets for lower/upper bounds.
        5. Compute feature explanations using TreeSHAP and Integrated Gradients.

        Args:
            pm25_records: Historical PM2.5 observation records.
            weather_records: Historical and current weather records.
            issue_at: Reference timestamp for the forecast run.

        Returns:
            Tuple of (list of 3 GeneratedForecast items, SHA-256 hash of input feature vector).
        """
        # Step 1: Verify artifact integrity
        self._verify_artifacts()

        # Step 2: Feature engineering
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

        # Step 3: Run inference per forecast horizon
        for raw_horizon, specification in self._manifest["horizons"].items():
            horizon = int(raw_horizon)
            try:
                # Load trained tree model artifact (XGBoost / LightGBM)
                tree = joblib.load(self._artifact_path(specification["tree_artifact"]))
                tree_prediction = float(tree.predict(row)[0])

                if specification["model_family"] == "XGBoost-GRU":
                    # Hybrid ensemble: combine Tree prediction with GRU neural network output
                    gru_prediction = self._predict_gru(specification["gru_artifact"], sequence)
                    weight = float(specification["xgboost_weight"])
                    prediction = weight * tree_prediction + (1 - weight) * gru_prediction
                else:
                    prediction = tree_prediction
            except (ForecastGenerationError, OSError, RuntimeError, ValueError, KeyError) as error:
                raise ForecastGenerationError("Required forecast model files are unavailable.") from error

            # Enforce non-negative PM2.5 physical constraint
            prediction = max(0.0, prediction)

            # Step 4: Conformal Prediction uncertainty intervals
            offset = float(specification["conformal_offset"])

            # Step 5: Explainable AI attribution calculation
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

        # Compute deterministic checksum of feature inputs for audit trail
        input_version = hashlib.sha256(
            np.asarray(
                [[entry[name] for name in tree_features] for entry in frame], dtype=np.float32
            ).tobytes()
        ).hexdigest()

        return sorted(forecasts, key=lambda item: item.horizon_hours), input_version

    def _load_manifest(self) -> dict[str, Any]:
        """Load and parse model_manifest.json containing model configuration and checksums."""
        path = Path(__file__).resolve().parents[2] / "model_manifest.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ForecastGenerationError("Forecast model manifest is unavailable.") from error

    def _artifact_path(self, filename: str) -> Path:
        """Resolve full filesystem path for a model artifact file."""
        return self._settings.model_artifact_directory / filename

    def _verify_artifacts(self) -> None:
        """Verify SHA-256 checksums of all model files against manifest to prevent corrupted models."""
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
        """Perform forward inference on the PyTorch GRU model with input/output scaling."""
        model, payload, scaled = self._load_gru(filename, sequence)
        with torch.no_grad():
            value = model(torch.tensor(scaled[None, :, :], dtype=torch.float32)).item()
        # Denormalize model output back to physical PM2.5 units (ug/m3)
        return float(value * payload["target_scale"] + payload["target_mean"])

    def _load_gru(self, filename: str, sequence: np.ndarray) -> tuple[GRURegressor, dict[str, Any], np.ndarray]:
        """Load PyTorch GRU checkpoint state and apply feature z-score normalization."""
        try:
            payload = torch.load(self._artifact_path(filename), map_location="cpu", weights_only=False)
            model = GRURegressor(len(payload["features"]))
            model.load_state_dict(payload["state_dict"])
        except (OSError, KeyError, RuntimeError, ValueError) as error:
            raise ForecastGenerationError("Required forecast model files are unavailable.") from error
        model.eval()
        # Standardize features using training set mean and scale
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
        """
        Generate feature importance explanations using TreeSHAP and Integrated Gradients.

        Verifies the SHAP Additive Completeness property:
        reconstructed_prediction = baseline_expected_value + sum(feature_contributions)
        If the reconstruction discrepancy exceeds 0.25 ug/m3, an error is raised.
        """
        tree_base, tree_values = _tree_shap_values(tree, row)
        grouped_tree = _group_contributions(tree_feature_names, tree_values)

        if specification["model_family"] == "XGBoost-GRU":
            # For hybrid models, compute Integrated Gradients for GRU and blend with TreeSHAP
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

        # Check SHAP completeness property
        reconstructed = baseline + sum(grouped.values())
        error = abs(prediction - reconstructed)
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
        """
        Compute Integrated Gradients attribution for PyTorch GRU recurrent neural network.

        Interpolates 256 steps between an all-zero baseline and the actual input tensor,
        accumulating the gradients to calculate exact feature importance attributions.
        """
        model, payload, scaled = self._load_gru(filename, sequence)
        inputs = torch.tensor(scaled, dtype=torch.float32)
        baseline = torch.zeros_like(inputs)
        total_gradients = torch.zeros_like(inputs)

        # Numerical path integration (Gauss-Legendre approximation over 256 steps)
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
    """
    Construct complete 169-hour tabular feature matrix.

    Generates:
    - PM2.5 hourly historical averages.
    - Weather metrics (temperature, humidity, pressure, precipitation, solar radiation, wind).
    - Trigonometric wind direction (sin/cos of angle).
    - Diurnal cyclical encoding: sin/cos(2 * pi * hour / 24).
    - Seasonal cyclical encoding: sin/cos(2 * pi * day_of_year / 365.25).
    - Multi-step lag features (T-1, T-2, T-3, T-6, T-12, T-24, T-48, T-72, T-168).
    """
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

        # Combine physical metrics and cyclical temporal encodings
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

    # Attach lagged PM2.5 features
    for index, item in enumerate(values):
        for lag in manifest["pm25_lags"]:
            item[f"pm25_lag_{lag}"] = values[index - lag]["pm25"] if index >= lag else float("nan")

    return values


def _tree_feature_names(manifest: dict[str, Any]) -> list[str]:
    """Extract ordered list of feature column names expected by tree models."""
    return [f"pm25_lag_{lag}" for lag in manifest["pm25_lags"]] + [
        name for name in manifest["base_features"] if name != "pm25"
    ]


def _tree_shap_values(tree: Any, row: np.ndarray) -> tuple[float, np.ndarray]:
    """Calculate exact TreeSHAP values for an XGBoost or scikit-learn tree artifact."""
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
    """Create initial zeroed dictionary for all 12 factor categories."""
    return {key: 0.0 for key, _label, _features in FACTOR_DEFINITIONS}


def _group_contributions(feature_names: list[str], values: np.ndarray) -> dict[str, float]:
    """Aggregate individual feature SHAP values into the 12 public factor categories."""
    grouped = _empty_groups()
    for name, value in zip(feature_names, values, strict=True):
        factor = FACTOR_BY_FEATURE.get(name)
        if factor is not None:
            grouped[factor] += float(value)
    return grouped


def _group_sequence_contributions(feature_names: list[str], values: np.ndarray) -> dict[str, float]:
    """Aggregate 24-hour GRU sequence attributions into the 12 public factor categories."""
    grouped = _empty_groups()
    for index, name in enumerate(feature_names):
        if name == "pm25":
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
    """
    Format and rank all 12 factors for UI visualization.

    Calculates:
    - Contribution in ug/m3.
    - Direction: 'increased', 'decreased', or 'neutral'.
    - Relative share percentage of total absolute contribution.
    - Top-3 indicator flag for highlighted UI badges.
    """
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
    """Round floating-point values to 2 decimal places using Decimal ROUND_HALF_UP."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
