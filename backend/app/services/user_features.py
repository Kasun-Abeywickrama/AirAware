"""
Service: User Features, Activity Planner, and Chart History.

This module provides high-level user-facing features:
1. Forecast & Observation History: Combines historical PM2.5 measurements with model predictions
   for interactive chart visualization and performance comparison.
2. Exposure-Aware Activity Planner: Sliding-window optimization algorithm that evaluates future
   consecutive forecast hours and ranks time intervals by lowest predicted PM2.5 exposure.
3. Anonymous Alert Preferences: Stores browser-specific PM2.5 thresholds without requiring user accounts.
"""

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


# Reference timezone for target date window alignment
NEW_DELHI_TIMEZONE = ZoneInfo("Asia/Kolkata")

# Mandatory advisory notice accompanying activity recommendations
PLANNER_DISCLAIMER = (
    "Comparative timing guidance only; this is not a safety guarantee or medical advice."
)


def _location(session):
    """Fetch the default configured active monitoring location."""
    settings = get_settings()
    return MonitoringLocationRepository(session).get_by_provider_location_id(
        "openaq", str(settings.openaq_location_id)
    )


def get_forecast_history(hours: int) -> PublicDataResult:
    """
    Assemble historical PM2.5 observations alongside issued model forecasts.

    Enables the frontend to plot 'Actual Observations vs Model Predictions' charts,
    allowing users to visually evaluate historical model accuracy.

    Args:
        hours: Number of past hours to retrieve (e.g., 24, 72, 168).

    Returns:
        PublicDataResult containing time series arrays of observations and forecasts.
    """
    if not database.check_database_connection():
        return unavailable("History is temporarily unavailable.", "DATABASE_UNAVAILABLE")
    try:
        session = database.get_session_factory()()
        try:
            location = _location(session)
            if location is None or not location.active:
                return unavailable("History is not available yet.", "HISTORY_NOT_AVAILABLE")

            since = datetime.now(timezone.utc) - timedelta(hours=hours)

            # Query historical ground-truth PM2.5 readings
            observations = Pm25ObservationRepository(session).list_since(
                location_id=location.id, since=since
            )

            # Query historical predictions targeting the same time window
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
    """
    Recommend optimal outdoor activity windows on a target date by minimizing PM2.5 exposure.

    Sliding Window Algorithm:
    1. Filter all forecast records targeting the requested 24-hour date.
    2. Slide a window of size `duration_hours` (e.g. 1h, 2h, 4h) across consecutive unbroken hourly forecasts.
    3. Calculate the mean predicted PM2.5 value and mean conformal upper bound for each window.
    4. Rank windows in ascending order of exposure (cleanest air first, with upper bound as tie-breaker).
    5. Return the top 5 recommended time slots with health disclaimer.

    Args:
        requested_date: Target calendar date in local timezone.
        duration_minutes: Duration of planned activity (in minutes, multiple of 60).
        now: Optional current timestamp reference.

    Returns:
        PublicDataResult containing ranked window recommendations.
    """
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

            # Retrieve forecasts falling inside the target date
            pairs = ForecastRepository(session).list_for_target_range(
                start_at=start_local.astimezone(timezone.utc),
                end_at=end_local.astimezone(timezone.utc),
                location_id=location_id,
            )
            latest_by_target = _latest_by_target(pairs)

            # Filter only future time slots
            future = [
                item for item in latest_by_target.values() if item[0].target_at >= comparison_time
            ]

            # Execute sliding-window ranking
            duration_hours = duration_minutes // 60
            windows = _rank_windows(future, duration_hours)

            if not windows:
                return unavailable("No complete forecast window is available for this date.", "PLAN_NOT_AVAILABLE")

            return PublicDataResult(
                200,
                {
                    "status": "available",
                    "date": requested_date,
                    "duration_minutes": duration_minutes,
                    "windows": windows[:5],  # Top 5 recommended windows
                    "disclaimer": PLANNER_DISCLAIMER,
                },
            )
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("Activity planning is temporarily unavailable.", "DATABASE_UNAVAILABLE")


def get_alert_preference(browser_id: UUID) -> PublicDataResult:
    """
    Retrieve stored alert preference for an anonymous browser client.

    Args:
        browser_id: Unique anonymous client identifier UUID.

    Returns:
        PublicDataResult with preference settings or default not_configured state.
    """
    if not database.check_database_connection():
        return unavailable("Alert preferences are temporarily unavailable.", "DATABASE_UNAVAILABLE")
    try:
        session = database.get_session_factory()()
        try:
            preference = AlertPreferenceRepository(session).get(browser_id)
            if preference is None:
                return PublicDataResult(
                    200,
                    {
                        "status": "not_configured",
                        "browser_id": browser_id,
                        "enabled": False,
                        "threshold_ug_m3": None,
                        "updated_at": None,
                    },
                )
            return PublicDataResult(200, _preference_item(preference))
        finally:
            session.close()
    except (RuntimeError, SQLAlchemyError):
        return unavailable("Alert preferences are temporarily unavailable.", "DATABASE_UNAVAILABLE")


def save_alert_preference(
    *, browser_id: UUID, threshold_ug_m3: Decimal, enabled: bool
) -> PublicDataResult:
    """
    Create or update PM2.5 alert threshold preference for an anonymous browser client.

    Args:
        browser_id: Anonymous browser client UUID.
        threshold_ug_m3: Concentration threshold in ug/m3.
        enabled: Boolean flag to enable or disable alerts.

    Returns:
        PublicDataResult with updated preference details.
    """
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
    """Deduplicate forecast pairs by target timestamp, selecting latest issued forecast."""
    latest = {}
    for forecast, run in pairs:
        latest.setdefault(forecast.target_at, (forecast, run))
    return latest


def _forecast_item(forecast, issued_at: datetime) -> dict[str, Any]:
    """Format single forecast record for public API response."""
    return {
        "issued_at": issued_at,
        "target_at": forecast.target_at,
        "horizon_hours": forecast.horizon_hours,
        "predicted_value_ug_m3": forecast.predicted_value_ug_m3,
        "lower_bound_ug_m3": forecast.lower_bound_ug_m3,
        "upper_bound_ug_m3": forecast.upper_bound_ug_m3,
    }


def _rank_windows(pairs, duration_hours: int) -> list[dict[str, Any]]:
    """
    Evaluate all consecutive candidate windows of duration_hours and rank by lowest exposure.

    Steps:
    1. Sort forecasts chronologically.
    2. Check that consecutive hours form an unbroken sequence (each +1 hour apart).
    3. Compute window mean predicted PM2.5 and mean upper bound.
    4. Sort windows: lowest mean predicted value first, then lowest upper bound.
    """
    ordered = sorted(pairs, key=lambda item: item[0].target_at)
    windows = []
    for start in range(0, len(ordered) - duration_hours + 1):
        group = ordered[start : start + duration_hours]
        times = [item[0].target_at for item in group]

        # Verify continuity of time window (must be strictly consecutive hourly steps)
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

    # Primary sort: lowest mean PM2.5; Secondary sort: lowest uncertainty upper bound
    return sorted(
        windows,
        key=lambda item: (item["mean_predicted_value_ug_m3"], item["mean_upper_bound_ug_m3"]),
    )


def _preference_item(preference) -> dict[str, Any]:
    """Format an AlertPreference model into a public dictionary payload."""
    return {
        "status": "configured",
        "browser_id": preference.browser_id,
        "threshold_ug_m3": preference.threshold_ug_m3,
        "enabled": preference.enabled,
        "updated_at": preference.updated_at,
    }
