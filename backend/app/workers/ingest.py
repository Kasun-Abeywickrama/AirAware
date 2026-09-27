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
        adapter = OpenAQAdapter(settings)
        latest = adapter.latest_pm25()
        if datetime.now(timezone.utc) - latest.observed_at > timedelta(
            minutes=settings.maximum_observation_age_minutes
        ):
            raise InputValidationError("PM2.5 observation is stale.")

        readings_by_time = {
            reading.observed_at: reading
            for reading in adapter.hourly_pm25_history(settings.pm25_history_hours)
        }
        readings_by_time[latest.observed_at] = latest
        validated_readings = [
            (
                reading.observed_at,
                validate_pm25_input(
                    value_ug_m3=reading.value_ug_m3,
                    unit=reading.unit,
                    observed_at=reading.observed_at,
                ),
            )
            for reading in readings_by_time.values()
        ]

        repository = Pm25ObservationRepository(session)
        created_count = 0
        for observed_at, value in validated_readings:
            _, created = repository.create_if_absent(
                location_id=location_id,
                ingestion_run_id=run.id,
                observed_at=observed_at,
                value_ug_m3=value,
            )
            created_count += int(created)
        runs.mark_succeeded(run)
        events.record(
            component="pm25_ingestion",
            level="info",
            message=(
                "PM2.5 ingestion completed."
                if created_count
                else "PM2.5 ingestion completed with no new observations."
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
        validated_readings = [
            (
                reading,
                validate_weather_input(
                    temperature_c=reading.temperature_c,
                    humidity_percent=reading.humidity_percent,
                    wind_speed_kmh=reading.wind_speed_kmh,
                    dew_point_c=reading.dew_point_c,
                    surface_pressure_hpa=reading.surface_pressure_hpa,
                    precipitation_mm=reading.precipitation_mm,
                    shortwave_radiation_w_m2=reading.shortwave_radiation_w_m2,
                    wind_direction_degrees=reading.wind_direction_degrees,
                    valid_at=reading.valid_at,
                ),
            )
            for reading in readings
        ]
        repository = WeatherRecordRepository(session)
        created_count = 0
        for reading, values in validated_readings:
            _, created = repository.create_or_update(
                location_id=location_id,
                ingestion_run_id=run.id,
                valid_at=reading.valid_at,
                temperature_c=values[0],
                humidity_percent=values[1],
                wind_speed_kmh=values[2],
                dew_point_c=values[3],
                surface_pressure_hpa=values[4],
                precipitation_mm=values[5],
                shortwave_radiation_w_m2=values[6],
                wind_direction_degrees=values[7],
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
