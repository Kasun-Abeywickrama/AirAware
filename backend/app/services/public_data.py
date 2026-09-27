"""Safe public read models for current conditions and saved forecasts."""

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
    """A public payload and HTTP code with only safe messages."""

    http_status_code: int
    payload: dict[str, Any]


def unavailable(message: str, code: str) -> PublicDataResult:
    return PublicDataResult(
        http_status_code=503,
        payload={"status": "unavailable", "message": message, "code": code},
    )


def get_current_conditions(now: datetime | None = None) -> PublicDataResult:
    """Return the latest approved PM2.5 value only when it is still fresh."""
    if not database.check_database_connection():
        return unavailable("Current conditions are temporarily unavailable.", "DATABASE_UNAVAILABLE")

    try:
        settings = get_settings()
        comparison_time = now or datetime.now(timezone.utc)
        session = database.get_session_factory()()
        try:
            location = MonitoringLocationRepository(session).get_by_provider_location_id(
                "openaq", str(settings.openaq_location_id)
            )
            if location is None or not location.active:
                return unavailable("Current conditions are not available yet.", "LOCATION_NOT_READY")
            observation = Pm25ObservationRepository(session).get_latest_for_location(location.id)
            if observation is None:
                return unavailable("Current conditions are not available yet.", "PM25_NOT_AVAILABLE")
            if observation.observed_at < comparison_time - timedelta(
                minutes=settings.maximum_observation_age_minutes
            ):
                return unavailable("Current PM2.5 data is stale.", "STALE_PM25_DATA")
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
    """Return one complete successful three-horizon forecast run, if present."""
    if not database.check_database_connection():
        return unavailable("Forecasts are temporarily unavailable.", "DATABASE_UNAVAILABLE")

    try:
        session = database.get_session_factory()()
        try:
            run = ForecastRunRepository(session).latest_succeeded()
            if run is None:
                return unavailable("Forecasts are not available yet.", "FORECASTS_NOT_AVAILABLE")
            forecasts = ForecastRepository(session).list_for_run(run.id)
            if {item.horizon_hours for item in forecasts} != {1, 6, 24}:
                return unavailable("Forecasts are not available yet.", "FORECASTS_NOT_AVAILABLE")
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
                        }
                        for item in forecasts
                    ],
                },
            )
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("Forecasts are temporarily unavailable.", "DATABASE_UNAVAILABLE")
