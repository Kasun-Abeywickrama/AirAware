"""Queries for approved weather records."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.weather_record import WeatherRecord


class WeatherRecordRepository:
    """Store and retrieve approved weather inputs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_approved(
        self,
        *,
        location_id: UUID,
        ingestion_run_id: UUID,
        valid_at: datetime,
        temperature_c: Decimal,
        humidity_percent: Decimal,
        wind_speed_kmh: Decimal,
    ) -> WeatherRecord:
        """Store one validated weather record in the application units."""
        record = WeatherRecord(
            location_id=location_id,
            ingestion_run_id=ingestion_run_id,
            valid_at=valid_at,
            temperature_c=temperature_c,
            humidity_percent=humidity_percent,
            wind_speed_kmh=wind_speed_kmh,
        )
        self._session.add(record)
        self._session.flush()
        return record

    def get_latest_for_location(self, location_id: UUID) -> WeatherRecord | None:
        """Return the newest weather record for one location."""
        statement = (
            select(WeatherRecord)
            .where(WeatherRecord.location_id == location_id)
            .order_by(WeatherRecord.valid_at.desc())
            .limit(1)
        )
        return self._session.scalar(statement)

    def create_if_absent(
        self,
        *,
        location_id: UUID,
        ingestion_run_id: UUID,
        valid_at: datetime,
        temperature_c: Decimal,
        humidity_percent: Decimal,
        wind_speed_kmh: Decimal,
    ) -> tuple[WeatherRecord, bool]:
        """Store an approved weather record unless the location/time already exists."""
        existing = self._session.scalar(
            select(WeatherRecord).where(
                WeatherRecord.location_id == location_id,
                WeatherRecord.valid_at == valid_at,
            )
        )
        if existing is not None:
            return existing, False

        return (
            self.create_approved(
                location_id=location_id,
                ingestion_run_id=ingestion_run_id,
                valid_at=valid_at,
                temperature_c=temperature_c,
                humidity_percent=humidity_percent,
                wind_speed_kmh=wind_speed_kmh,
            ),
            True,
        )
