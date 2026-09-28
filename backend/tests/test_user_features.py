from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import CheckConstraint, UniqueConstraint

from backend.app.api.routes import activity_plans as activity_route
from backend.app.api.routes import alert_preferences as alert_route
from backend.app.api.routes import forecasts as forecast_route
from backend.app.main import app
from backend.app.models.alert_preference import AlertPreference
from backend.app.repositories.alert_preferences import AlertPreferenceRepository
from backend.app.services.public_data import PublicDataResult
from backend.app.services.user_features import NEW_DELHI_TIMEZONE, _rank_windows


NOW = datetime(2026, 9, 28, 10, tzinfo=timezone.utc)
BROWSER_ID = UUID("00000000-0000-0000-0000-000000000140")
client = TestClient(app)


def pair(hour: int, upper: str):
    forecast = SimpleNamespace(
        target_at=NOW + timedelta(hours=hour),
        predicted_value_ug_m3=Decimal("60"),
        upper_bound_ug_m3=Decimal(upper),
    )
    return forecast, SimpleNamespace(issued_at=NOW)


def test_activity_windows_are_ranked_by_mean_upper_bound() -> None:
    windows = _rank_windows([pair(1, "100"), pair(2, "80"), pair(3, "60")], 2)

    assert len(windows) == 2
    assert windows[0]["start_at"] == (NOW + timedelta(hours=2)).astimezone(NEW_DELHI_TIMEZONE)
    assert windows[0]["comparative_score"] == 70


def test_activity_windows_require_consecutive_forecasts() -> None:
    assert _rank_windows([pair(1, "80"), pair(3, "60")], 2) == []


def test_alert_preference_model_has_anonymous_unique_id_and_range() -> None:
    names = {constraint.name for constraint in AlertPreference.__table__.constraints}

    assert "uq_alert_preferences_browser_id" in names
    assert "ck_alert_preferences_threshold_range" in names
    assert sum(isinstance(item, UniqueConstraint) for item in AlertPreference.__table__.constraints) == 1
    assert sum(isinstance(item, CheckConstraint) for item in AlertPreference.__table__.constraints) == 1


def test_alert_preference_repository_creates_then_updates_same_browser() -> None:
    class Session:
        def __init__(self):
            self.preference = None
            self.added = []
            self.flush_count = 0

        def scalar(self, statement):
            return self.preference

        def add(self, item):
            self.added.append(item)
            self.preference = item

        def flush(self):
            self.flush_count += 1

    session = Session()
    repository = AlertPreferenceRepository(session)
    created = repository.upsert(
        browser_id=BROWSER_ID, threshold_ug_m3=Decimal("70"), enabled=True
    )
    updated = repository.upsert(
        browser_id=BROWSER_ID, threshold_ug_m3=Decimal("80"), enabled=False
    )

    assert created is updated
    assert updated.threshold_ug_m3 == Decimal("80")
    assert updated.enabled is False
    assert len(session.added) == 1


def test_history_route_enforces_hour_limit() -> None:
    response = client.get("/api/v1/forecasts/history?hours=169")

    assert response.status_code == 422


def test_activity_route_rejects_non_hourly_duration() -> None:
    response = client.post(
        "/api/v1/activity-plans", json={"date": str(date(2026, 9, 28)), "duration_minutes": 90}
    )

    assert response.status_code == 422


def test_public_feature_routes_return_safe_payloads(monkeypatch) -> None:
    monkeypatch.setattr(
        forecast_route,
        "get_forecast_history",
        lambda hours: PublicDataResult(503, {"status": "unavailable", "code": "HISTORY_NOT_AVAILABLE", "message": "History is not available yet."}),
    )
    monkeypatch.setattr(
        activity_route,
        "create_activity_plan",
        lambda **kwargs: PublicDataResult(503, {"status": "unavailable", "code": "PLAN_NOT_AVAILABLE", "message": "No complete forecast window is available for this date."}),
    )
    monkeypatch.setattr(
        alert_route,
        "get_alert_preference",
        lambda browser_id: PublicDataResult(200, {"status": "not_configured", "browser_id": browser_id, "enabled": False, "threshold_ug_m3": None, "updated_at": None}),
    )
    monkeypatch.setattr(
        alert_route,
        "save_alert_preference",
        lambda **kwargs: PublicDataResult(200, {"status": "configured", "browser_id": kwargs["browser_id"], "enabled": kwargs["enabled"], "threshold_ug_m3": kwargs["threshold_ug_m3"], "updated_at": NOW}),
    )

    history = client.get("/api/v1/forecasts/history")
    plan = client.post("/api/v1/activity-plans", json={"date": "2026-09-28", "duration_minutes": 60})
    preference = client.get(f"/api/v1/alert-preferences/{BROWSER_ID}")
    update = client.put(
        f"/api/v1/alert-preferences/{BROWSER_ID}",
        json={"threshold_ug_m3": 70, "enabled": True},
    )

    assert history.status_code == 503
    assert plan.status_code == 503
    assert plan.json()["code"] == "PLAN_NOT_AVAILABLE"
    assert preference.json()["status"] == "not_configured"
    assert update.status_code == 200
    assert update.json()["threshold_ug_m3"] == 70
