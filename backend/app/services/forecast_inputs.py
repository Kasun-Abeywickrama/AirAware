"""Readiness checks for the existing packaged operational forecast models."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models.pm25_observation import Pm25Observation
from ..models.weather_record import WeatherRecord


PM25_LAG_HOURS = 168
WEATHER_SEQUENCE_HOURS = 24
MODEL_WEATHER_FIELDS = (
    "temperature_c",
    "humidity_percent",
    "wind_speed_kmh",
    "dew_point_c",
    "surface_pressure_hpa",
    "precipitation_mm",
    "shortwave_radiation_w_m2",
    "wind_direction_degrees",
)


@dataclass(frozen=True)
class ForecastInputReadiness:
    """Whether stored live records satisfy the packaged model input contract."""

    ready: bool
    reason: str | None
    issue_at: datetime | None


def _hour_start(value: datetime, station_timezone: ZoneInfo) -> datetime:
    """Map a provider timestamp to the station's local model hour."""
    return value.astimezone(station_timezone).replace(minute=0, second=0, microsecond=0)


def evaluate_forecast_input_records(
    *,
    pm25_records: Iterable[Pm25Observation],
    weather_records: Iterable[WeatherRecord],
    settings: Settings,
    now: datetime | None = None,
) -> ForecastInputReadiness:
    """Evaluate records without loading any model artifact or exposing raw diagnostics."""
    station_timezone = ZoneInfo(settings.station_timezone)
    pm25_by_hour: dict[datetime, Pm25Observation] = {}
    latest: Pm25Observation | None = None
    for record in pm25_records:
        hour = _hour_start(record.observed_at, station_timezone)
        current = pm25_by_hour.get(hour)
        if current is None or record.observed_at > current.observed_at:
            pm25_by_hour[hour] = record
        if latest is None or record.observed_at > latest.observed_at:
            latest = record

    if latest is None:
        return ForecastInputReadiness(False, "PM2.5 history is not available.", None)

    comparison_time = now or datetime.now(timezone.utc)
    if latest.observed_at < comparison_time - timedelta(
        minutes=settings.maximum_observation_age_minutes
    ):
        return ForecastInputReadiness(False, "Recent PM2.5 data is stale.", None)

    issue_at = _hour_start(latest.observed_at, station_timezone)
    required_pm25_hours = {
        issue_at - timedelta(hours=offset) for offset in range(PM25_LAG_HOURS + 1)
    }
    if not required_pm25_hours.issubset(pm25_by_hour):
        return ForecastInputReadiness(False, "Recent 168-hour PM2.5 history is incomplete.", issue_at)

    weather_by_hour = {
        _hour_start(record.valid_at, station_timezone): record for record in weather_records
    }
    required_weather_hours = {
        issue_at - timedelta(hours=offset) for offset in range(WEATHER_SEQUENCE_HOURS)
    }
    for hour in required_weather_hours:
        record = weather_by_hour.get(hour)
        if record is None or any(getattr(record, field) is None for field in MODEL_WEATHER_FIELDS):
            return ForecastInputReadiness(
                False,
                "Required 24-hour weather history is incomplete.",
                issue_at,
            )

    return ForecastInputReadiness(True, None, issue_at)


def check_forecast_input_readiness(
    session: Session,
    *,
    location_id: UUID,
    settings: Settings,
    now: datetime | None = None,
) -> ForecastInputReadiness:
    """Load one location's records and apply the forecast input contract."""
    pm25_records = session.scalars(
        select(Pm25Observation).where(Pm25Observation.location_id == location_id)
    ).all()
    weather_records = session.scalars(
        select(WeatherRecord).where(WeatherRecord.location_id == location_id)
    ).all()
    return evaluate_forecast_input_records(
        pm25_records=pm25_records,
        weather_records=weather_records,
        settings=settings,
        now=now,
    )
