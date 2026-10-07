"""Repository for querying and managing monitoring locations.

Encapsulates database operations for active air quality monitoring stations.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models.monitoring_location import MonitoringLocation


class MonitoringLocationRepository:
    """Data access layer for the 'monitoring_locations' table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_provider_location_id(
        self,
        provider: str,
        provider_location_id: str,
    ) -> MonitoringLocation | None:
        """Find a monitoring station by provider name and provider location ID."""
        statement = select(MonitoringLocation).where(
            MonitoringLocation.provider == provider,
            MonitoringLocation.provider_location_id == provider_location_id,
        )
        return self._session.scalar(statement)

    def list_active(self) -> list[MonitoringLocation]:
        """Fetch all active monitoring stations ordered alphabetically by name."""
        statement = (
            select(MonitoringLocation)
            .where(MonitoringLocation.active.is_(True))
            .order_by(MonitoringLocation.name)
        )
        return list(self._session.scalars(statement).all())

    def upsert_configured_openaq_location(self, settings: Settings) -> MonitoringLocation:
        """Insert or update the configured OpenAQ station to prevent duplicates.

        If the station exists, its coordinates, timezone, and active flag are updated.
        If it does not exist, a new MonitoringLocation record is inserted.
        """
        location = self.get_by_provider_location_id(
            "openaq",
            str(settings.openaq_location_id),
        )
        if location is None:
            # Create a new station record
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
            # Update existing station metadata
            location.name = settings.station_name
            location.latitude = settings.station_latitude
            location.longitude = settings.station_longitude
            location.timezone = settings.station_timezone
            location.active = True

        self._session.flush()
        return location
