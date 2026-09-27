"""Manual live data ingestion command."""

from datetime import datetime, timedelta, timezone

from ..adapters import OpenAQAdapter, OpenMeteoAdapter, ProviderError
from ..config import Settings, get_settings
from ..database import get_session_factory
from ..repositories.ingestion_runs import IngestionRunRepository
from ..repositories.monitoring_locations import MonitoringLocationRepository
from ..repositories.pm25_observations import Pm25ObservationRepository
from ..repositories.system_events import SystemEventRepository
from ..repositories.weather_records import WeatherRecordRepository
from ..services.validation import InputValidationError, validate_pm25_input, validate_weather_input


def ingest_all(settings: Settings | None = None) -> bool:
    """Fetch both providers once, recording their independent outcomes."""
    active_settings = settings or get_settings()
    session = get_session_factory()()
    try:
        location = MonitoringLocationRepository(session).upsert_configured_openaq_location(active_settings)
        session.commit()

        pm25_success = _ingest_pm25(session, location.id, active_settings)
        weather_success = _ingest_weather(session, location.id, active_settings)
        return pm25_success and weather_success
    finally:
        session.close()


def _ingest_pm25(session, location_id, settings: Settings) -> bool:
    runs = IngestionRunRepository(session)
    events = SystemEventRepository(session)
    run = runs.start("pm25")
    try:
        reading = OpenAQAdapter(settings).latest_pm25()
        value = validate_pm25_input(
            value_ug_m3=reading.value_ug_m3,
            unit=reading.unit,
            observed_at=reading.observed_at,
        )
        if datetime.now(timezone.utc) - reading.observed_at > timedelta(
            minutes=settings.maximum_observation_age_minutes
        ):
            raise InputValidationError("PM2.5 observation is stale.")
        _, created = Pm25ObservationRepository(session).create_if_absent(
            location_id=location_id,
            ingestion_run_id=run.id,
            observed_at=reading.observed_at,
            value_ug_m3=value,
        )
        runs.mark_succeeded(run)
        events.record(
            component="pm25_ingestion",
            level="info",
            message=(
                "PM2.5 ingestion completed."
                if created
                else "PM2.5 ingestion completed with no new observation."
            ),
        )
        session.commit()
        return True
    except (InputValidationError, ProviderError):
        runs.mark_failed(run, "PM2.5 ingestion failed.")
        events.record(
            component="pm25_ingestion",
            level="warning",
            message="PM2.5 ingestion failed.",
        )
        session.commit()
        return False


def _ingest_weather(session, location_id, settings: Settings) -> bool:
    runs = IngestionRunRepository(session)
    events = SystemEventRepository(session)
    run = runs.start("weather")
    try:
        readings = OpenMeteoAdapter(settings).hourly_weather()
        repository = WeatherRecordRepository(session)
        created_count = 0
        for reading in readings:
            temperature, humidity, wind_speed = validate_weather_input(
                temperature_c=reading.temperature_c,
                humidity_percent=reading.humidity_percent,
                wind_speed_kmh=reading.wind_speed_kmh,
                valid_at=reading.valid_at,
            )
            _, created = repository.create_if_absent(
                location_id=location_id,
                ingestion_run_id=run.id,
                valid_at=reading.valid_at,
                temperature_c=temperature,
                humidity_percent=humidity,
                wind_speed_kmh=wind_speed,
            )
            created_count += int(created)
        runs.mark_succeeded(run)
        events.record(
            component="weather_ingestion",
            level="info",
            message=(
                "Weather ingestion completed."
                if created_count
                else "Weather ingestion completed with no new records."
            ),
        )
        session.commit()
        return True
    except (InputValidationError, ProviderError):
        runs.mark_failed(run, "Weather ingestion failed.")
        events.record(
            component="weather_ingestion",
            level="warning",
            message="Weather ingestion failed.",
        )
        session.commit()
        return False


if __name__ == "__main__":
    raise SystemExit(0 if ingest_all() else 1)
