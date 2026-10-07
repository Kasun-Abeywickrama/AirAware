"""
Worker: Live Data Ingestion Pipeline.

This module automates data acquisition from external environmental APIs:
1. OpenAQ: Real-time PM2.5 measurements and 168-hour history.
2. Open-Meteo: Hourly meteorological metrics (temperature, humidity, wind, pressure, precipitation, solar radiation).

It performs rigorous data validation and logs audit records to `IngestionRun` and `SystemEvent` tables.
"""

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
    """
    Execute full ingestion cycle for both PM2.5 and Weather providers.

    Workflow:
    1. Upsert monitoring station metadata in database.
    2. Ingest real-time and historical PM2.5 data from OpenAQ.
    3. Ingest meteorological parameters from Open-Meteo.
    4. Record execution status and log audit events.

    Args:
        settings: Application configuration settings.

    Returns:
        True if both providers succeeded, False if any provider encountered an error.
    """
    active_settings = settings or get_settings()
    session = get_session_factory()()
    try:
        # Ensure active monitoring location is registered in DB
        location = MonitoringLocationRepository(session).upsert_configured_openaq_location(active_settings)
        session.commit()

        # Run independent provider ingestions
        pm25_success = _ingest_pm25(session, location.id, active_settings)
        weather_success = _ingest_weather(session, location.id, active_settings)
        return pm25_success and weather_success
    finally:
        session.close()


def _ingest_pm25(session, location_id, settings: Settings) -> bool:
    """
    Fetch, validate, and store PM2.5 observations from OpenAQ API.

    Enforces staleness guardrails and deduplication.
    """
    runs = IngestionRunRepository(session)
    events = SystemEventRepository(session)
    run = runs.start("pm25")
    try:
        adapter = OpenAQAdapter(settings)
        latest = adapter.latest_pm25()

        # Check staleness guardrail
        if datetime.now(timezone.utc) - latest.observed_at > timedelta(
            minutes=settings.maximum_observation_age_minutes
        ):
            raise InputValidationError("PM2.5 observation is stale.")

        # Fetch 168+ hours of history for ML model lag window
        readings_by_time = {
            reading.observed_at: reading
            for reading in adapter.hourly_pm25_history(settings.pm25_history_hours + 2)
        }
        readings_by_time[latest.observed_at] = latest

        # Validate PM2.5 values (non-negative, numeric, timezone-aware)
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

        # Insert new observation records (idempotent upsert)
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

        # Mark job as succeeded in audit table
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
        # Gracefully handle validation failure or network timeout
        runs.mark_failed(run, "PM2.5 ingestion failed.")
        events.record(
            component="pm25_ingestion",
            level="warning",
            message="PM2.5 ingestion failed.",
        )
        session.commit()
        return False


def _ingest_weather(session, location_id, settings: Settings) -> bool:
    """
    Fetch, validate, and store 8 meteorological parameters from Open-Meteo API.

    Parameters:
    - Temperature, Humidity, Wind Speed, Dew Point, Surface Pressure, Precipitation,
      Shortwave Solar Radiation, Wind Direction.
    """
    runs = IngestionRunRepository(session)
    events = SystemEventRepository(session)
    run = runs.start("weather")
    try:
        readings = OpenMeteoAdapter(settings).hourly_weather()

        # Validate all physical weather boundaries
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

        # Store weather records in database
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

        # Mark job as succeeded
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
        # Gracefully handle failure
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
