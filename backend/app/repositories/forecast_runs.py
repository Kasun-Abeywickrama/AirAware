"""State changes for operational forecast runs."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.forecast_run import ForecastRun


class ForecastRunRepository:
    """Create and complete forecast generation audit records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def start(self, *, issued_at: datetime, model_version: str) -> ForecastRun:
        run = ForecastRun(issued_at=issued_at, model_version=model_version, status="running")
        self._session.add(run)
        self._session.flush()
        return run

    def mark_succeeded(self, run: ForecastRun, *, input_version: str) -> ForecastRun:
        run.status = "succeeded"
        run.input_version = input_version
        run.failure_reason = None
        run.completed_at = datetime.now(timezone.utc)
        self._session.flush()
        return run

    def mark_failed(self, run: ForecastRun, reason: str) -> ForecastRun:
        run.status = "failed"
        run.failure_reason = reason
        run.completed_at = datetime.now(timezone.utc)
        self._session.flush()
        return run

    def latest_succeeded(self) -> ForecastRun | None:
        return self._session.scalar(
            select(ForecastRun)
            .where(ForecastRun.status == "succeeded")
            .order_by(ForecastRun.issued_at.desc())
            .limit(1)
        )

    def get_latest(self) -> ForecastRun | None:
        return self._session.scalar(
            select(ForecastRun).order_by(ForecastRun.issued_at.desc()).limit(1)
        )
