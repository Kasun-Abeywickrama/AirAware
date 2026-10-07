"""Repository for PM2.5 observation data access.

Handles persistence, deduplication, latest reading queries, and time-series fetching.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.pm25_observation import Pm25Observation


class Pm25ObservationRepository:
    """Data access layer for the 'pm25_observations' table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_approved(
        self,
        *,
        location_id: UUID,
        ingestion_run_id: UUID,
        observed_at: datetime,
        value_ug_m3: Decimal,
    ) -> Pm25Observation:
        """Insert a single verified PM2.5 observation into the database."""
        observation = Pm25Observation(
            location_id=location_id,
            ingestion_run_id=ingestion_run_id,
            observed_at=observed_at,
            value_ug_m3=value_ug_m3,
            unit="ug/m3",
        )
        self._session.add(observation)
        self._session.flush()
        return observation

    def get_latest_for_location(self, location_id: UUID) -> Pm25Observation | None:
        """Fetch the most recent PM2.5 reading for a monitoring station."""
        statement = (
            select(Pm25Observation)
            .where(Pm25Observation.location_id == location_id)
            .order_by(Pm25Observation.observed_at.desc())
            .limit(1)
        )
        return self._session.scalar(statement)

    def create_if_absent(
        self,
        *,
        location_id: UUID,
        ingestion_run_id: UUID,
        observed_at: datetime,
        value_ug_m3: Decimal,
    ) -> tuple[Pm25Observation, bool]:
        """Insert observation only if no record exists for (location_id, observed_at).

        Returns a tuple: (observation_record, was_inserted_boolean).
        Used during batch history ingestion to avoid duplicate row conflicts.
        """
        existing = self._session.scalar(
            select(Pm25Observation).where(
                Pm25Observation.location_id == location_id,
                Pm25Observation.observed_at == observed_at,
            )
        )
        if existing is not None:
            return existing, False

        return (
            self.create_approved(
                location_id=location_id,
                ingestion_run_id=ingestion_run_id,
                observed_at=observed_at,
                value_ug_m3=value_ug_m3,
            ),
            True,
        )

    def list_since(self, *, location_id: UUID, since: datetime) -> list[Pm25Observation]:
        """Fetch chronological observations from a given timestamp onwards for charts."""
        statement = (
            select(Pm25Observation)
            .where(
                Pm25Observation.location_id == location_id,
                Pm25Observation.observed_at >= since,
            )
            .order_by(Pm25Observation.observed_at)
        )
        return list(self._session.scalars(statement).all())
