"""Queries for monitoring locations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.monitoring_location import MonitoringLocation


class MonitoringLocationRepository:
    """Read monitoring locations for future ingestion workflows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_provider_location_id(
        self,
        provider: str,
        provider_location_id: str,
    ) -> MonitoringLocation | None:
        """Return a location matching its provider identifier, if present."""
        statement = select(MonitoringLocation).where(
            MonitoringLocation.provider == provider,
            MonitoringLocation.provider_location_id == provider_location_id,
        )
        return self._session.scalar(statement)

    def list_active(self) -> list[MonitoringLocation]:
        """Return active locations in a stable name order."""
        statement = (
            select(MonitoringLocation)
            .where(MonitoringLocation.active.is_(True))
            .order_by(MonitoringLocation.name)
        )
        return list(self._session.scalars(statement).all())
