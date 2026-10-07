"""Repository for data ingestion run audit records.

Tracks lifecycle events (start, success, failure) for hourly PM2.5 and weather data jobs.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.ingestion_run import IngestionRun


class IngestionRunRepository:
    """Data access layer for the 'ingestion_runs' table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def start(self, source_type: str) -> IngestionRun:
        """Create a new IngestionRun record in 'running' status."""
        run = IngestionRun(source_type=source_type, status="running")
        self._session.add(run)
        self._session.flush()
        return run

    def mark_succeeded(self, run: IngestionRun) -> IngestionRun:
        """Mark an ingestion run as 'succeeded' and record its completion timestamp."""
        run.status = "succeeded"
        run.completed_at = datetime.now(timezone.utc)
        run.failure_reason = None
        self._session.flush()
        return run

    def mark_failed(self, run: IngestionRun, reason: str) -> IngestionRun:
        """Mark an ingestion run as 'failed' with a diagnostic error message."""
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.failure_reason = reason
        self._session.flush()
        return run

    def get_latest(self, source_type: str) -> IngestionRun | None:
        """Fetch the most recent ingestion run for a given source ('pm25' or 'weather')."""
        statement = (
            select(IngestionRun)
            .where(IngestionRun.source_type == source_type)
            .order_by(IngestionRun.started_at.desc())
            .limit(1)
        )
        return self._session.scalar(statement)
