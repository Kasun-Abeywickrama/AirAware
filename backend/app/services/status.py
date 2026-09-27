"""Safe public availability summaries."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypedDict

from sqlalchemy.exc import SQLAlchemyError

from .. import database
from ..models.ingestion_run import IngestionRun
from ..repositories.ingestion_runs import IngestionRunRepository


SourceAvailability = Literal["available", "not_started", "unavailable"]


class SourceStatus(TypedDict):
    status: SourceAvailability
    last_completed_at: datetime | None


class PublicStatusPayload(TypedDict):
    status: Literal["available", "limited"]
    database: Literal["connected", "unreachable"]
    pm25: SourceStatus
    weather: SourceStatus


@dataclass(frozen=True)
class PublicStatusResult:
    """Safe status payload plus the correct HTTP response code."""

    http_status_code: int
    payload: PublicStatusPayload


def source_status(run: IngestionRun | None) -> SourceStatus:
    """Translate an ingestion audit record into a public-safe summary."""
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
) -> PublicStatusResult:
    """Build a public status response without exposing diagnostic details."""
    if not database_connected:
        unavailable: SourceStatus = {"status": "unavailable", "last_completed_at": None}
        return PublicStatusResult(
            http_status_code=503,
            payload={
                "status": "limited",
                "database": "unreachable",
                "pm25": unavailable,
                "weather": unavailable,
            },
        )

    pm25 = source_status(pm25_run)
    weather = source_status(weather_run)
    overall_status: Literal["available", "limited"] = (
        "available"
        if pm25["status"] == "available" and weather["status"] == "available"
        else "limited"
    )
    return PublicStatusResult(
        http_status_code=200,
        payload={
            "status": overall_status,
            "database": "connected",
            "pm25": pm25,
            "weather": weather,
        },
    )


def get_public_status() -> PublicStatusResult:
    """Read live database and ingestion state for the public status endpoint."""
    if not database.check_database_connection():
        return build_public_status(database_connected=False)

    try:
        session = database.get_session_factory()()
        try:
            repository = IngestionRunRepository(session)
            return build_public_status(
                database_connected=True,
                pm25_run=repository.get_latest("pm25"),
                weather_run=repository.get_latest("weather"),
            )
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return build_public_status(database_connected=False)
