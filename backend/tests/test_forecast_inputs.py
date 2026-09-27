from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from backend.app.config import Settings
from backend.app.models.pm25_observation import Pm25Observation
from backend.app.models.weather_record import WeatherRecord
from backend.app.services.forecast_inputs import evaluate_forecast_input_records


LOCATION_ID = UUID("00000000-0000-0000-0000-000000000110")
RUN_ID = UUID("00000000-0000-0000-0000-000000000111")
ISSUE_AT = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)


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


def pm25_history() -> list[Pm25Observation]:
    return [
        Pm25Observation(
            location_id=LOCATION_ID,
            ingestion_run_id=RUN_ID,
            observed_at=ISSUE_AT - timedelta(hours=offset),
            value_ug_m3=Decimal("60"),
            unit="ug/m3",
        )
        for offset in range(169)
    ]


def weather_history() -> list[WeatherRecord]:
    return [
        WeatherRecord(
            location_id=LOCATION_ID,
            ingestion_run_id=RUN_ID,
            valid_at=ISSUE_AT - timedelta(hours=offset),
            temperature_c=Decimal("31"),
            humidity_percent=Decimal("72"),
            wind_speed_kmh=Decimal("10"),
            dew_point_c=Decimal("25"),
            surface_pressure_hpa=Decimal("1004"),
            precipitation_mm=Decimal("0"),
            shortwave_radiation_w_m2=Decimal("500"),
            wind_direction_degrees=Decimal("180"),
        )
        for offset in range(24)
    ]


def test_forecast_inputs_are_ready_for_packaged_models() -> None:
    result = evaluate_forecast_input_records(
        pm25_records=pm25_history(),
        weather_records=weather_history(),
        settings=settings(),
        now=ISSUE_AT + timedelta(minutes=30),
    )

    assert result.ready is True
    assert result.reason is None
    assert result.issue_at == ISSUE_AT


def test_forecast_inputs_reject_missing_pm25_history() -> None:
    result = evaluate_forecast_input_records(
        pm25_records=pm25_history()[:-1],
        weather_records=weather_history(),
        settings=settings(),
        now=ISSUE_AT + timedelta(minutes=30),
    )

    assert result.ready is False
    assert result.reason == "Recent 168-hour PM2.5 history is incomplete."


def test_forecast_inputs_reject_missing_model_weather_field() -> None:
    weather = weather_history()
    weather[0].surface_pressure_hpa = None
    result = evaluate_forecast_input_records(
        pm25_records=pm25_history(),
        weather_records=weather,
        settings=settings(),
        now=ISSUE_AT + timedelta(minutes=30),
    )

    assert result.ready is False
    assert result.reason == "Required 24-hour weather history is incomplete."


def test_forecast_inputs_reject_stale_latest_pm25() -> None:
    result = evaluate_forecast_input_records(
        pm25_records=pm25_history(),
        weather_records=weather_history(),
        settings=settings(),
        now=ISSUE_AT + timedelta(hours=4),
    )

    assert result.ready is False
    assert result.reason == "Recent PM2.5 data is stale."
