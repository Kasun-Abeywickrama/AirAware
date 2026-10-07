"""
Service: Public Data Assembler.

This module provides safe, sanitized read-only data for the public API endpoints:
1. Current real-time air quality conditions (with staleness guardrails).
2. Latest ML forecast runs across 1h, 6h, and 24h horizons (with conformal bounds and XAI explanations).

It ensures that database failures or missing/stale records gracefully return
structured unavailable status payloads rather than crashing the API.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from ..config import get_settings
from .. import database
from ..repositories.forecast_runs import ForecastRunRepository
from ..repositories.forecasts import ForecastRepository
from ..repositories.monitoring_locations import MonitoringLocationRepository
from ..repositories.pm25_observations import Pm25ObservationRepository


@dataclass(frozen=True)
class PublicDataResult:
    """Standard container for public endpoint response payloads and HTTP status codes."""

    http_status_code: int
    payload: dict[str, Any]


def unavailable(message: str, code: str) -> PublicDataResult:
    """
    Construct a standardized HTTP 503 unavailable payload.

    Args:
        message: User-friendly English explanation.
        code: Machine-readable error code for frontend logic.

    Returns:
        PublicDataResult configured with HTTP 503 status.
    """
    return PublicDataResult(
        http_status_code=503,
        payload={"status": "unavailable", "message": message, "code": code},
    )


def get_current_conditions(now: datetime | None = None) -> PublicDataResult:
    """
    Fetch the latest valid PM2.5 measurement for the default active monitoring station.

    Guardrail Rules:
    - Verifies database connectivity.
    - Confirms station exists and is active.
    - Checks staleness: If the reading is older than `maximum_observation_age_minutes`
      (e.g., 180 minutes), it returns 'STALE_PM25_DATA' to prevent showing obsolete readings.

    Args:
        now: Optional reference timestamp (defaults to UTC now).

    Returns:
        PublicDataResult with HTTP 200 (if fresh) or HTTP 503 (if stale/unavailable).
    """
    if not database.check_database_connection():
        return unavailable("Current conditions are temporarily unavailable.", "DATABASE_UNAVAILABLE")

    try:
        settings = get_settings()
        comparison_time = now or datetime.now(timezone.utc)
        session = database.get_session_factory()()
        try:
            # 1. Fetch active station record
            location = MonitoringLocationRepository(session).get_by_provider_location_id(
                "openaq", str(settings.openaq_location_id)
            )
            if location is None or not location.active:
                return unavailable("Current conditions are not available yet.", "LOCATION_NOT_READY")

            # 2. Fetch latest PM2.5 observation
            observation = Pm25ObservationRepository(session).get_latest_for_location(location.id)
            if observation is None:
                return unavailable("Current conditions are not available yet.", "PM25_NOT_AVAILABLE")

            # 3. Check staleness guardrail (e.g. 180 min threshold)
            if observation.observed_at < comparison_time - timedelta(
                minutes=settings.maximum_observation_age_minutes
            ):
                return unavailable("Current PM2.5 data is stale.", "STALE_PM25_DATA")

            # 4. Return fresh PM2.5 observation
            return PublicDataResult(
                http_status_code=200,
                payload={
                    "status": "available",
                    "pm25": {
                        "value_ug_m3": observation.value_ug_m3,
                        "unit": observation.unit,
                        "observed_at": observation.observed_at,
                        "received_at": observation.received_at,
                    },
                    "source": {
                        "provider": location.provider,
                        "location_name": location.name,
                    },
                },
            )
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("Current conditions are temporarily unavailable.", "DATABASE_UNAVAILABLE")


def get_latest_forecasts() -> PublicDataResult:
    """
    Fetch the latest successful forecast run containing all 3 prediction horizons (1h, 6h, 24h).

    Validation Rules:
    - Requires a completed ForecastRun with status 'succeeded'.
    - Must contain forecasts for exactly horizons {1, 6, 24}.
    - Includes point estimates, conformal uncertainty bounds, and XAI feature importance factors.

    Returns:
        PublicDataResult with HTTP 200 payload or HTTP 503 unavailable.
    """
    if not database.check_database_connection():
        return unavailable("Forecasts are temporarily unavailable.", "DATABASE_UNAVAILABLE")

    try:
        settings = get_settings()
        session = database.get_session_factory()()
        try:
            # 1. Identify active monitoring location
            location = None
            try:
                location = MonitoringLocationRepository(session).get_by_provider_location_id(
                    "openaq", str(settings.openaq_location_id)
                )
            except Exception:
                location = None
            location_id = location.id if location else None

            # 2. Get latest successful forecast run
            try:
                run = ForecastRunRepository(session).latest_succeeded(location_id=location_id)
            except TypeError:
                run = ForecastRunRepository(session).latest_succeeded()

            if run is None:
                return unavailable("Forecasts are not available yet.", "FORECASTS_NOT_AVAILABLE")

            # 3. Fetch predictions and verify all 3 horizons are present
            forecasts = ForecastRepository(session).list_for_run(run.id)
            if {item.horizon_hours for item in forecasts} != {1, 6, 24}:
                return unavailable("Forecasts are not available yet.", "FORECASTS_NOT_AVAILABLE")

            # 4. Attach explainable AI (XAI) factors for each horizon
            explanation_by_forecast = ForecastRepository(session).explanations_for_forecasts(
                [item.id for item in forecasts]
            )

            return PublicDataResult(
                http_status_code=200,
                payload={
                    "status": "available",
                    "issued_at": run.issued_at,
                    "model_version": run.model_version,
                    "forecasts": [
                        {
                            "horizon_hours": item.horizon_hours,
                            "target_at": item.target_at,
                            "predicted_value_ug_m3": item.predicted_value_ug_m3,
                            "lower_bound_ug_m3": item.lower_bound_ug_m3,
                            "upper_bound_ug_m3": item.upper_bound_ug_m3,
                            "explanation": _public_explanation(explanation_by_forecast.get(item.id)),
                        }
                        for item in forecasts
                    ],
                },
            )
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("Forecasts are temporarily unavailable.", "DATABASE_UNAVAILABLE")


def _public_explanation(explanation: Any | None) -> dict[str, Any] | None:
    """
    Format explainable AI feature importance factors for public display.

    Includes a scientific disclaimer stating that learned model correlations
    represent statistical relationships rather than direct physical causation.

    Args:
        explanation: ForecastExplanation database record or None.

    Returns:
        Formatted dictionary with factors list and disclaimer notice, or None.
    """
    if explanation is None:
        return None
    return {
        "factors": explanation.factors,
        "notice": "These show patterns learned by the model, not proven causes of pollution.",
    }
