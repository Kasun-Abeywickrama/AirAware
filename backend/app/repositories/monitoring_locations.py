"""Queries for monitoring locations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
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

    def upsert_configured_openaq_location(self, settings: Settings) -> MonitoringLocation:
        """Create or update the configured OpenAQ station without duplicate rows."""
        location = self.get_by_provider_location_id(
            "openaq",
            str(settings.openaq_location_id),
        )
        if location is None:
            location = MonitoringLocation(
                name=settings.station_name,
                provider="openaq",
                provider_location_id=str(settings.openaq_location_id),
                latitude=settings.station_latitude,
                longitude=settings.station_longitude,
                timezone=settings.station_timezone,
                active=True,
            )
            self._session.add(location)
        else:
            location.name = settings.station_name
            location.latitude = settings.station_latitude
            location.longitude = settings.station_longitude
            location.timezone = settings.station_timezone
            location.active = True

        self._session.flush()
        return location
