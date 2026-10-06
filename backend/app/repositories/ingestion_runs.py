"""Queries and state changes for ingestion audit records."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.ingestion_run import IngestionRun


class IngestionRunRepository:
    """Create and update data-collection audit records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def start(self, source_type: str) -> IngestionRun:
        """Create a running audit record for one data source type."""
        run = IngestionRun(source_type=source_type, status="running")
        self._session.add(run)
        self._session.flush()
        return run

    def mark_succeeded(self, run: IngestionRun) -> IngestionRun:
        """Mark an audit record as completed successfully."""
        run.status = "succeeded"
        run.completed_at = datetime.now(timezone.utc)
        run.failure_reason = None
        self._session.flush()
        return run

    def mark_failed(self, run: IngestionRun, reason: str) -> IngestionRun:
        """Mark an audit record as failed with a safe diagnostic reason."""
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.failure_reason = reason
        self._session.flush()
        return run

    def get_latest(self, source_type: str) -> IngestionRun | None:
        """Return the latest audit record for PM2.5 or weather."""
        statement = (
            select(IngestionRun)
            .where(IngestionRun.source_type == source_type)
            .order_by(IngestionRun.started_at.desc())
            .limit(1)
        )
        return self._session.scalar(statement)
