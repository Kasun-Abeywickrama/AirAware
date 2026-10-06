from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.forecast_run import ForecastRun


class ForecastRunRepository:
    """Create and complete forecast generation audit records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def start(
        self,
        *,
        issued_at: datetime,
        model_version: str,
        location_id: UUID | None = None,
    ) -> ForecastRun:
        run = ForecastRun(
            issued_at=issued_at,
            model_version=model_version,
            status="running",
            location_id=location_id,
        )
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

    def latest_succeeded(self, location_id: UUID | None = None) -> ForecastRun | None:
        statement = select(ForecastRun).where(ForecastRun.status == "succeeded")
        if location_id is not None:
            station_run = self._session.scalar(
                statement.where(ForecastRun.location_id == location_id)
                .order_by(ForecastRun.issued_at.desc())
                .limit(1)
            )
            if station_run is not None:
                return station_run
            return self._session.scalar(
                statement.where(ForecastRun.location_id.is_(None))
                .order_by(ForecastRun.issued_at.desc())
                .limit(1)
            )
        return self._session.scalar(
            statement.order_by(ForecastRun.issued_at.desc()).limit(1)
        )

    def get_latest(self, location_id: UUID | None = None) -> ForecastRun | None:
        statement = select(ForecastRun)
        if location_id is not None:
            station_run = self._session.scalar(
                statement.where(ForecastRun.location_id == location_id)
                .order_by(ForecastRun.issued_at.desc())
                .limit(1)
            )
            if station_run is not None:
                return station_run
            return self._session.scalar(
                statement.where(ForecastRun.location_id.is_(None))
                .order_by(ForecastRun.issued_at.desc())
                .limit(1)
            )
        return self._session.scalar(
            statement.order_by(ForecastRun.issued_at.desc()).limit(1)
        )
