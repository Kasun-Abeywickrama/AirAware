"""Queries for approved weather records."""

from datetime import datetime, timezone
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
        dew_point_c: Decimal,
        surface_pressure_hpa: Decimal,
        precipitation_mm: Decimal,
        shortwave_radiation_w_m2: Decimal,
        wind_direction_degrees: Decimal,
    ) -> WeatherRecord:
        """Store one validated weather record in the application units."""
        record = WeatherRecord(
            location_id=location_id,
            ingestion_run_id=ingestion_run_id,
            valid_at=valid_at,
            temperature_c=temperature_c,
            humidity_percent=humidity_percent,
            wind_speed_kmh=wind_speed_kmh,
            dew_point_c=dew_point_c,
            surface_pressure_hpa=surface_pressure_hpa,
            precipitation_mm=precipitation_mm,
            shortwave_radiation_w_m2=shortwave_radiation_w_m2,
            wind_direction_degrees=wind_direction_degrees,
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

    def create_or_update(
        self,
        *,
        location_id: UUID,
        ingestion_run_id: UUID,
        valid_at: datetime,
        temperature_c: Decimal,
        humidity_percent: Decimal,
        wind_speed_kmh: Decimal,
        dew_point_c: Decimal,
        surface_pressure_hpa: Decimal,
        precipitation_mm: Decimal,
        shortwave_radiation_w_m2: Decimal,
        wind_direction_degrees: Decimal,
    ) -> tuple[WeatherRecord, bool]:
        """Store or refresh the newest approved weather value for a location/time."""
        existing = self._session.scalar(
            select(WeatherRecord).where(
                WeatherRecord.location_id == location_id,
                WeatherRecord.valid_at == valid_at,
            )
        )
        if existing is not None:
            existing.ingestion_run_id = ingestion_run_id
            existing.temperature_c = temperature_c
            existing.humidity_percent = humidity_percent
            existing.wind_speed_kmh = wind_speed_kmh
            existing.dew_point_c = dew_point_c
            existing.surface_pressure_hpa = surface_pressure_hpa
            existing.precipitation_mm = precipitation_mm
            existing.shortwave_radiation_w_m2 = shortwave_radiation_w_m2
            existing.wind_direction_degrees = wind_direction_degrees
            existing.received_at = datetime.now(timezone.utc)
            self._session.flush()
            return existing, False

        return (
            self.create_approved(
                location_id=location_id,
                ingestion_run_id=ingestion_run_id,
                valid_at=valid_at,
                temperature_c=temperature_c,
                humidity_percent=humidity_percent,
                wind_speed_kmh=wind_speed_kmh,
                dew_point_c=dew_point_c,
                surface_pressure_hpa=surface_pressure_hpa,
                precipitation_mm=precipitation_mm,
                shortwave_radiation_w_m2=shortwave_radiation_w_m2,
                wind_direction_degrees=wind_direction_degrees,
            ),
            True,
        )
