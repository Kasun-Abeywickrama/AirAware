from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

from backend.app.adapters import Pm25Reading, ProviderError, WeatherReading
from backend.app.config import Settings
from backend.app.workers import ingest


LOCATION_ID = UUID("00000000-0000-0000-0000-000000000100")
PM25_RUN_ID = UUID("00000000-0000-0000-0000-000000000101")
WEATHER_RUN_ID = UUID("00000000-0000-0000-0000-000000000102")
NOW = datetime.now(timezone.utc)


def settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused",
        openaq_api_key="test-key",
        openaq_location_id=8118,
        openaq_sensor_id=23534,
        station_name="New Delhi PM2.5 Station",
        station_latitude=28.63576,
        station_longitude=77.22445,
        station_timezone="Asia/Kolkata",
        provider_timeout_seconds=20,
        maximum_observation_age_minutes=180,
        pm25_history_hours=168,
    )


class FakeSession:
    def __init__(self):
        self.events = []
        self.commits = 0
        self.closed = False

    def commit(self) -> None:
        self.commits += 1

    def close(self) -> None:
        self.closed = True


class FakeLocationRepository:
    def __init__(self, session):
        self.session = session

    def upsert_configured_openaq_location(self, settings):
        return SimpleNamespace(id=LOCATION_ID)


class FakeRunRepository:
    def __init__(self, session):
        self.session = session

    def start(self, source_type):
        return SimpleNamespace(
            id=PM25_RUN_ID if source_type == "pm25" else WEATHER_RUN_ID,
            source_type=source_type,
            status="running",
        )

    def mark_succeeded(self, run):
        run.status = "succeeded"
        return run

    def mark_failed(self, run, reason):
        run.status = "failed"
        run.failure_reason = reason
        return run


class FakeEventRepository:
    def __init__(self, session):
        self.session = session

    def record(self, **event):
        self.session.events.append(event)


class FakePm25Repository:
    def __init__(self, session):
        self.session = session

    def create_if_absent(self, **kwargs):
        return SimpleNamespace(**kwargs), True


class FakeWeatherRepository:
    def __init__(self, session):
        self.session = session

    def create_or_update(self, **kwargs):
        return SimpleNamespace(**kwargs), True


def configure_worker_fakes(monkeypatch, session) -> None:
    monkeypatch.setattr(ingest, "get_session_factory", lambda: lambda: session)
    monkeypatch.setattr(ingest, "MonitoringLocationRepository", FakeLocationRepository)
    monkeypatch.setattr(ingest, "IngestionRunRepository", FakeRunRepository)
    monkeypatch.setattr(ingest, "SystemEventRepository", FakeEventRepository)
    monkeypatch.setattr(ingest, "Pm25ObservationRepository", FakePm25Repository)
    monkeypatch.setattr(ingest, "WeatherRecordRepository", FakeWeatherRepository)


def test_manual_ingestion_records_success_for_both_sources(monkeypatch) -> None:
    session = FakeSession()
    configure_worker_fakes(monkeypatch, session)

    monkeypatch.setattr(
        ingest.OpenAQAdapter,
        "latest_pm25",
        lambda self: Pm25Reading(NOW, Decimal("62.4"), "ug/m3"),
    )
    monkeypatch.setattr(
        ingest.OpenAQAdapter,
        "hourly_pm25_history",
        lambda self, hours: [Pm25Reading(NOW, Decimal("62.4"), "ug/m3")],
    )
    monkeypatch.setattr(
        ingest.OpenMeteoAdapter,
        "hourly_weather",
        lambda self: [
            WeatherReading(
                NOW, Decimal("31.5"), Decimal("72"), Decimal("10.2"), Decimal("25"),
                Decimal("1004"), Decimal("0"), Decimal("500"), Decimal("180"),
            )
        ],
    )

    assert ingest.ingest_all(settings()) is True
    assert [event["component"] for event in session.events] == [
        "pm25_ingestion",
        "weather_ingestion",
    ]
    assert all(event["level"] == "info" for event in session.events)
    assert session.closed is True


def test_weather_runs_even_when_pm25_provider_fails(monkeypatch) -> None:
    session = FakeSession()
    configure_worker_fakes(monkeypatch, session)

    def failed_pm25(self):
        raise ProviderError("OpenAQ request failed.")

    monkeypatch.setattr(ingest.OpenAQAdapter, "latest_pm25", failed_pm25)
    monkeypatch.setattr(ingest.OpenAQAdapter, "hourly_pm25_history", lambda self, hours: [])
    monkeypatch.setattr(
        ingest.OpenMeteoAdapter,
        "hourly_weather",
        lambda self: [
            WeatherReading(
                NOW, Decimal("31.5"), Decimal("72"), Decimal("10.2"), Decimal("25"),
                Decimal("1004"), Decimal("0"), Decimal("500"), Decimal("180"),
            )
        ],
    )

    assert ingest.ingest_all(settings()) is False
    assert [event["component"] for event in session.events] == [
        "pm25_ingestion",
        "weather_ingestion",
    ]
    assert session.events[0]["level"] == "warning"
    assert session.events[1]["level"] == "info"
