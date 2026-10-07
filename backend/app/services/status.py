"""
Service: System Health and Pipeline Status Monitoring.

This module aggregates operational health across all core AirAware subsystems:
- Database connectivity
- Real-time PM2.5 ingestion pipeline
- Numerical weather ingestion pipeline
- Background ML forecast model execution

It translates backend audit records into user-safe health summaries without exposing internal server errors.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypedDict

from sqlalchemy.exc import SQLAlchemyError

from .. import database
from ..config import get_settings
from ..models.ingestion_run import IngestionRun
from ..models.forecast_run import ForecastRun
from ..repositories.forecast_runs import ForecastRunRepository
from ..repositories.ingestion_runs import IngestionRunRepository
from ..repositories.monitoring_locations import MonitoringLocationRepository


# Possible component availability states
SourceAvailability = Literal["available", "not_started", "unavailable"]


class SourceStatus(TypedDict):
    """Status dictionary for an individual data ingestion or forecast pipeline."""

    status: SourceAvailability
    last_completed_at: datetime | None


class PublicStatusPayload(TypedDict):
    """Complete aggregated system status response payload."""

    status: Literal["available", "limited"]
    database: Literal["connected", "unreachable"]
    pm25: SourceStatus
    weather: SourceStatus
    forecast: SourceStatus


@dataclass(frozen=True)
class PublicStatusResult:
    """Container holding public status response data and appropriate HTTP response code."""

    http_status_code: int
    payload: PublicStatusPayload


def source_status(run: IngestionRun | ForecastRun | None) -> SourceStatus:
    """
    Translate an internal job run record into a public-safe status summary.

    Args:
        run: IngestionRun or ForecastRun record, or None if no run exists yet.

    Returns:
        SourceStatus with 'available', 'not_started', or 'unavailable'.
    """
    if run is None:
        return {"status": "not_started", "last_completed_at": None}

    if run.status == "succeeded":
        return {"status": "available", "last_completed_at": run.completed_at}

    return {"status": "unavailable", "last_completed_at": run.completed_at}


def build_public_status(
    *,
    database_connected: bool,
    pm25_run: IngestionRun | None = None,
    weather_run: IngestionRun | None = None,
    forecast_run: ForecastRun | None = None,
) -> PublicStatusResult:
    """
    Build the aggregated system health payload from component statuses.

    Rules:
    - If database is disconnected -> returns HTTP 503 with database='unreachable'.
    - If all 3 subsystems (pm25, weather, forecast) are 'available' -> overall='available' (HTTP 200).
    - If any subsystem has failed or is incomplete -> overall='limited' (HTTP 200).

    Args:
        database_connected: True if PostgreSQL ping succeeds.
        pm25_run: Most recent PM2.5 ingestion run record.
        weather_run: Most recent weather ingestion run record.
        forecast_run: Most recent forecast model run record.

    Returns:
        PublicStatusResult object.
    """
    if not database_connected:
        unavailable_source: SourceStatus = {"status": "unavailable", "last_completed_at": None}
        return PublicStatusResult(
            http_status_code=503,
            payload={
                "status": "limited",
                "database": "unreachable",
                "pm25": unavailable_source,
                "weather": unavailable_source,
                "forecast": unavailable_source,
            },
        )

    pm25 = source_status(pm25_run)
    weather = source_status(weather_run)
    forecast = source_status(forecast_run)

    # Check if all pipelines are healthy
    overall_status: Literal["available", "limited"] = (
        "available"
        if (
            pm25["status"] == "available"
            and weather["status"] == "available"
            and forecast["status"] == "available"
        )
        else "limited"
    )

    return PublicStatusResult(
        http_status_code=200,
        payload={
            "status": overall_status,
            "database": "connected",
            "pm25": pm25,
            "weather": weather,
            "forecast": forecast,
        },
    )


def get_public_status() -> PublicStatusResult:
    """
    Query the database to evaluate live system health and return status payload.

    Returns:
        PublicStatusResult with status summary and HTTP status code.
    """
    if not database.check_database_connection():
        return build_public_status(database_connected=False)

    try:
        session = database.get_session_factory()()
        try:
            repository = IngestionRunRepository(session)
            location = None
            try:
                settings = get_settings()
                location = MonitoringLocationRepository(session).get_by_provider_location_id(
                    "openaq", str(settings.openaq_location_id)
                )
            except Exception:
                location = None
            location_id = location.id if location else None

            try:
                forecast_run = ForecastRunRepository(session).get_latest(location_id=location_id)
            except TypeError:
                forecast_run = ForecastRunRepository(session).get_latest()

            return build_public_status(
                database_connected=True,
                pm25_run=repository.get_latest("pm25"),
                weather_run=repository.get_latest("weather"),
                forecast_run=forecast_run,
            )
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return build_public_status(database_connected=False)
