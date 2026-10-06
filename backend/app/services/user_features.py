"""Public history, activity-planning, and anonymous preference workflows."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.exc import SQLAlchemyError

from .. import database
from ..config import get_settings
from ..repositories.alert_preferences import AlertPreferenceRepository
from ..repositories.forecasts import ForecastRepository
from ..repositories.monitoring_locations import MonitoringLocationRepository
from ..repositories.pm25_observations import Pm25ObservationRepository
from .public_data import PublicDataResult, unavailable


NEW_DELHI_TIMEZONE = ZoneInfo("Asia/Kolkata")
PLANNER_DISCLAIMER = (
    "Comparative timing guidance only; this is not a safety guarantee or medical advice."
)


def _location(session):
    settings = get_settings()
    return MonitoringLocationRepository(session).get_by_provider_location_id(
        "openaq", str(settings.openaq_location_id)
    )


def get_forecast_history(hours: int) -> PublicDataResult:
    """Return bounded observation and forecast series for a frontend chart."""
    if not database.check_database_connection():
        return unavailable("History is temporarily unavailable.", "DATABASE_UNAVAILABLE")
    try:
        session = database.get_session_factory()()
        try:
            location = _location(session)
            if location is None or not location.active:
                return unavailable("History is not available yet.", "HISTORY_NOT_AVAILABLE")
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            observations = Pm25ObservationRepository(session).list_since(
                location_id=location.id, since=since
            )
            forecast_pairs = ForecastRepository(session).list_since(
                since, location_id=location.id
            )
            latest_by_target = _latest_by_target(forecast_pairs)
            if not observations and not latest_by_target:
                return unavailable("History is not available yet.", "HISTORY_NOT_AVAILABLE")
            return PublicDataResult(
                200,
                {
                    "status": "available",
                    "hours": hours,
                    "observations": [
                        {
                            "observed_at": item.observed_at,
                            "value_ug_m3": item.value_ug_m3,
                            "unit": item.unit,
                        }
                        for item in observations
                    ],
                    "forecasts": [
                        _forecast_item(forecast, run.issued_at)
                        for forecast, run in sorted(
                            latest_by_target.values(), key=lambda item: item[0].target_at
                        )
                    ],
                },
            )
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("History is temporarily unavailable.", "DATABASE_UNAVAILABLE")


def create_activity_plan(
    *, requested_date: date, duration_minutes: int, now: datetime | None = None
) -> PublicDataResult:
    """Rank complete future forecast windows for one New Delhi local date."""
    if not database.check_database_connection():
        return unavailable("Activity planning is temporarily unavailable.", "DATABASE_UNAVAILABLE")
    comparison_time = now or datetime.now(timezone.utc)
    start_local = datetime.combine(requested_date, datetime.min.time(), tzinfo=NEW_DELHI_TIMEZONE)
    end_local = start_local + timedelta(days=1)
    try:
        session = database.get_session_factory()()
        try:
            location = _location(session)
            location_id = location.id if location else None
            pairs = ForecastRepository(session).list_for_target_range(
                start_at=start_local.astimezone(timezone.utc),
                end_at=end_local.astimezone(timezone.utc),
                location_id=location_id,
            )
            latest_by_target = _latest_by_target(pairs)
            future = [
                item for item in latest_by_target.values() if item[0].target_at >= comparison_time
            ]
            windows = _rank_windows(future, duration_minutes // 60)
            if not windows:
                return unavailable("No complete forecast window is available for this date.", "PLAN_NOT_AVAILABLE")
            return PublicDataResult(
                200,
                {
                    "status": "available",
                    "date": requested_date,
                    "duration_minutes": duration_minutes,
                    "windows": windows[:5],
                    "disclaimer": PLANNER_DISCLAIMER,
                },
            )
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("Activity planning is temporarily unavailable.", "DATABASE_UNAVAILABLE")


def get_alert_preference(browser_id: UUID) -> PublicDataResult:
    """Read one anonymous browser's alert preference."""
    if not database.check_database_connection():
        return unavailable("Alert preferences are temporarily unavailable.", "DATABASE_UNAVAILABLE")
    try:
        session = database.get_session_factory()()
        try:
            preference = AlertPreferenceRepository(session).get(browser_id)
            if preference is None:
                return PublicDataResult(
                    200,
                    {"status": "not_configured", "browser_id": browser_id, "enabled": False,
                     "threshold_ug_m3": None, "updated_at": None},
                )
            return PublicDataResult(200, _preference_item(preference))
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("Alert preferences are temporarily unavailable.", "DATABASE_UNAVAILABLE")


def save_alert_preference(
    *, browser_id: UUID, threshold_ug_m3: Decimal, enabled: bool
) -> PublicDataResult:
    """Create or update a preference without any notification side effect."""
    if not database.check_database_connection():
        return unavailable("Alert preferences are temporarily unavailable.", "DATABASE_UNAVAILABLE")
    try:
        session = database.get_session_factory()()
        try:
            preference = AlertPreferenceRepository(session).upsert(
                browser_id=browser_id, threshold_ug_m3=threshold_ug_m3, enabled=enabled
            )
            session.commit()
            return PublicDataResult(200, _preference_item(preference))
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("Alert preferences are temporarily unavailable.", "DATABASE_UNAVAILABLE")


def _latest_by_target(pairs):
    latest = {}
    for forecast, run in pairs:
        latest.setdefault(forecast.target_at, (forecast, run))
    return latest


def _forecast_item(forecast, issued_at: datetime) -> dict[str, Any]:
    return {
        "issued_at": issued_at,
        "target_at": forecast.target_at,
        "horizon_hours": forecast.horizon_hours,
        "predicted_value_ug_m3": forecast.predicted_value_ug_m3,
        "lower_bound_ug_m3": forecast.lower_bound_ug_m3,
        "upper_bound_ug_m3": forecast.upper_bound_ug_m3,
    }


def _rank_windows(pairs, duration_hours: int) -> list[dict[str, Any]]:
    ordered = sorted(pairs, key=lambda item: item[0].target_at)
    windows = []
    for start in range(0, len(ordered) - duration_hours + 1):
        group = ordered[start : start + duration_hours]
        times = [item[0].target_at for item in group]
        if any(later - earlier != timedelta(hours=1) for earlier, later in zip(times, times[1:])):
            continue
        points = [float(item[0].predicted_value_ug_m3) for item in group]
        uppers = [float(item[0].upper_bound_ug_m3) for item in group]
        mean_pred = sum(points) / len(points)
        mean_upper = sum(uppers) / len(uppers)
        windows.append(
            {
                "start_at": times[0].astimezone(NEW_DELHI_TIMEZONE),
                "end_at": (times[-1] + timedelta(hours=1)).astimezone(NEW_DELHI_TIMEZONE),
                "mean_predicted_value_ug_m3": mean_pred,
                "mean_upper_bound_ug_m3": mean_upper,
                "comparative_score": mean_pred,
                "rationale": "Ranked by lowest predicted PM2.5 concentration (cleanest air first).",
            }
        )
    return sorted(
        windows,
        key=lambda item: (item["mean_predicted_value_ug_m3"], item["mean_upper_bound_ug_m3"]),
    )


def _preference_item(preference) -> dict[str, Any]:
    return {
        "status": "configured",
        "browser_id": preference.browser_id,
        "threshold_ug_m3": preference.threshold_ug_m3,
        "enabled": preference.enabled,
        "updated_at": preference.updated_at,
    }
