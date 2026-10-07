"""
Service: ML Model Forecast Input Readiness Evaluator.

This module validates that stored database records meet the strict input requirements
of the operational Machine Learning models (GRU/XGBoost) before running inference.

Model Input Contract:
1. Freshness: Latest PM2.5 reading must not be stale (within configured age threshold).
2. PM2.5 Lags: Requires an unbroken 168-hour (7 days) historical time series of PM2.5 data.
3. Weather Features: Requires a continuous 24-hour sequence of all 8 meteorological parameters.
"""

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


# Required history window constants for ML feature engineering
PM25_LAG_HOURS = 168          # 7 days of historical PM2.5 lags
WEATHER_SEQUENCE_HOURS = 24   # 24 hours of sequential meteorological features

# All 8 weather parameters required by the ML model input matrix
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
    """
    Readiness assessment result for ML forecast model execution.

    Attributes:
        ready: True if all lag and weather requirements are satisfied, False otherwise.
        reason: Plain English explanation if readiness check fails.
        issue_at: The aligned reference hour for the forecast run (if available).
    """

    ready: bool
    reason: str | None
    issue_at: datetime | None


def _hour_start(value: datetime, station_timezone: ZoneInfo) -> datetime:
    """
    Truncate a datetime timestamp to the start of the hour in station local time.

    Args:
        value: Source timestamp.
        station_timezone: Timezone of the monitoring station (e.g. 'Asia/Colombo').

    Returns:
        Datetime truncated to minute=0, second=0, microsecond=0.
    """
    return value.astimezone(station_timezone).replace(minute=0, second=0, microsecond=0)


def evaluate_forecast_input_records(
    *,
    pm25_records: Iterable[Pm25Observation],
    weather_records: Iterable[WeatherRecord],
    settings: Settings,
    now: datetime | None = None,
) -> ForecastInputReadiness:
    """
    Evaluate in-memory records against the ML model input contract without loading model files.

    Checks:
    1. PM2.5 presence: At least one observation exists.
    2. Freshness: Latest observation is not stale (< maximum_observation_age_minutes).
    3. PM2.5 Continuity: Unbroken 168-hour history (T-0 through T-168).
    4. Weather Completeness: 24 consecutive hours of all 8 non-null weather fields.

    Args:
        pm25_records: Iterable of PM2.5 observations.
        weather_records: Iterable of weather records.
        settings: Application configuration settings.
        now: Optional reference timestamp (defaults to UTC now).

    Returns:
        ForecastInputReadiness indicating whether inference can proceed safely.
    """
    station_timezone = ZoneInfo(settings.station_timezone)
    pm25_by_hour: dict[datetime, Pm25Observation] = {}
    latest: Pm25Observation | None = None

    # Group PM2.5 observations by hour, keeping newest record per hour
    for record in pm25_records:
        hour = _hour_start(record.observed_at, station_timezone)
        current = pm25_by_hour.get(hour)
        if current is None or record.observed_at > current.observed_at:
            pm25_by_hour[hour] = record
        if latest is None or record.observed_at > latest.observed_at:
            latest = record

    # Step 1: Check if any PM2.5 data exists
    if latest is None:
        return ForecastInputReadiness(False, "PM2.5 history is not available.", None)

    # Step 2: Check staleness guardrail
    comparison_time = now or datetime.now(timezone.utc)
    if latest.observed_at < comparison_time - timedelta(
        minutes=settings.maximum_observation_age_minutes
    ):
        return ForecastInputReadiness(False, "Recent PM2.5 data is stale.", None)

    issue_at = _hour_start(latest.observed_at, station_timezone)

    # Step 3: Check 168-hour (7 day) unbroken PM2.5 history
    required_pm25_hours = {
        issue_at - timedelta(hours=offset) for offset in range(PM25_LAG_HOURS + 1)
    }
    if not required_pm25_hours.issubset(pm25_by_hour):
        return ForecastInputReadiness(False, "Recent 168-hour PM2.5 history is incomplete.", issue_at)

    # Step 4: Check 24-hour complete weather feature sequence
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

    # All input contract criteria met successfully
    return ForecastInputReadiness(True, None, issue_at)


def check_forecast_input_readiness(
    session: Session,
    *,
    location_id: UUID,
    settings: Settings,
    now: datetime | None = None,
) -> ForecastInputReadiness:
    """
    Query database for a station's observation & weather history and check ML model readiness.

    Args:
        session: Active database session.
        location_id: Monitoring station primary key UUID.
        settings: Application settings.
        now: Optional reference timestamp.

    Returns:
        ForecastInputReadiness result.
    """
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
