from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from backend.app.models.weather_record import WeatherRecord
from backend.app.repositories.weather_records import WeatherRecordRepository


LOCATION_ID = UUID("00000000-0000-0000-0000-000000000010")
INGESTION_RUN_ID = UUID("00000000-0000-0000-0000-000000000020")


class FakeSession:
    def __init__(self, latest_record=None):
        self.latest_record = latest_record
        self.added = []
        self.flush_count = 0

    def add(self, item) -> None:
        self.added.append(item)

    def flush(self) -> None:
        self.flush_count += 1

    def scalar(self, statement):
        return self.latest_record


def test_weather_record_has_required_constraints() -> None:
    table = WeatherRecord.__table__
    constraint_names = {constraint.name for constraint in table.constraints}

    assert "uq_weather_records_location_valid_at" in constraint_names
    assert "ck_weather_records_humidity_range" in constraint_names
    assert "ck_weather_records_non_negative_wind_speed" in constraint_names
    assert "ck_weather_records_wind_direction_range" in constraint_names
    assert sum(isinstance(item, ForeignKeyConstraint) for item in table.constraints) == 2
    assert sum(isinstance(item, UniqueConstraint) for item in table.constraints) == 1
    assert sum(isinstance(item, CheckConstraint) for item in table.constraints) == 6


def test_repository_creates_approved_weather_record() -> None:
    session = FakeSession()
    repository = WeatherRecordRepository(session)
    valid_at = datetime(2026, 9, 27, 10, tzinfo=timezone.utc)

    record = repository.create_approved(
        location_id=LOCATION_ID,
        ingestion_run_id=INGESTION_RUN_ID,
        valid_at=valid_at,
        temperature_c=Decimal("31.50"),
        humidity_percent=Decimal("72.00"),
        wind_speed_kmh=Decimal("10.20"),
        dew_point_c=Decimal("25.00"),
        surface_pressure_hpa=Decimal("1004.00"),
        precipitation_mm=Decimal("0.00"),
        shortwave_radiation_w_m2=Decimal("500.00"),
        wind_direction_degrees=Decimal("180.00"),
    )

    assert record.location_id == LOCATION_ID
    assert record.ingestion_run_id == INGESTION_RUN_ID
    assert record.valid_at == valid_at
    assert record.temperature_c == Decimal("31.50")
    assert record.humidity_percent == Decimal("72.00")
    assert record.wind_speed_kmh == Decimal("10.20")
    assert record.dew_point_c == Decimal("25.00")
    assert session.added == [record]
    assert session.flush_count == 1


def test_repository_returns_latest_weather_record_for_location() -> None:
    latest_record = WeatherRecord(
        location_id=LOCATION_ID,
        ingestion_run_id=INGESTION_RUN_ID,
        valid_at=datetime(2026, 9, 27, 10, tzinfo=timezone.utc),
        temperature_c=Decimal("31.50"),
        humidity_percent=Decimal("72.00"),
        wind_speed_kmh=Decimal("10.20"),
    )
    repository = WeatherRecordRepository(FakeSession(latest_record=latest_record))

    assert repository.get_latest_for_location(LOCATION_ID) is latest_record


def test_repository_refreshes_existing_weather_record() -> None:
    existing = WeatherRecord(
        location_id=LOCATION_ID,
        ingestion_run_id=INGESTION_RUN_ID,
        valid_at=datetime(2026, 9, 27, 10, tzinfo=timezone.utc),
        temperature_c=Decimal("31.50"),
        humidity_percent=Decimal("72.00"),
        wind_speed_kmh=Decimal("10.20"),
    )
    session = FakeSession(latest_record=existing)
    repository = WeatherRecordRepository(session)

    result, created = repository.create_or_update(
        location_id=LOCATION_ID,
        ingestion_run_id=INGESTION_RUN_ID,
        valid_at=existing.valid_at,
        temperature_c=existing.temperature_c,
        humidity_percent=existing.humidity_percent,
        wind_speed_kmh=existing.wind_speed_kmh,
        dew_point_c=Decimal("25.00"),
        surface_pressure_hpa=Decimal("1004.00"),
        precipitation_mm=Decimal("0.00"),
        shortwave_radiation_w_m2=Decimal("500.00"),
        wind_direction_degrees=Decimal("180.00"),
    )

    assert result is existing
    assert created is False
    assert session.added == []
    assert session.flush_count == 1
