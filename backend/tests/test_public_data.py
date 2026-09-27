from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.api.routes import conditions as conditions_route
from backend.app.api.routes import forecasts as forecasts_route
from backend.app.config import Settings
from backend.app.main import app
from backend.app.services import public_data
from backend.app.services.public_data import PublicDataResult


NOW = datetime(2026, 9, 28, 10, tzinfo=timezone.utc)
LOCATION_ID = UUID("00000000-0000-0000-0000-000000000130")
RUN_ID = UUID("00000000-0000-0000-0000-000000000131")
client = TestClient(app)


def settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused", openaq_api_key="test-key",
        openaq_location_id=8118, openaq_sensor_id=23534,
        station_name="New Delhi PM2.5 Station", station_latitude=28.63576,
        station_longitude=77.22445, station_timezone="Asia/Kolkata",
        provider_timeout_seconds=20, maximum_observation_age_minutes=180,
        pm25_history_hours=168,
    )


class FakeSession:
    def close(self) -> None:
        return None


def configure_database(monkeypatch) -> None:
    monkeypatch.setattr(public_data.database, "check_database_connection", lambda: True)
    monkeypatch.setattr(public_data.database, "get_session_factory", lambda: lambda: FakeSession())


def test_current_conditions_returns_fresh_approved_observation(monkeypatch) -> None:
    configure_database(monkeypatch)
    monkeypatch.setattr(public_data, "get_settings", settings)
    monkeypatch.setattr(
        public_data, "MonitoringLocationRepository",
        lambda session: SimpleNamespace(
            get_by_provider_location_id=lambda provider, location_id: SimpleNamespace(
                id=LOCATION_ID, active=True, provider="openaq", name="New Delhi PM2.5 Station"
            )
        ),
    )
    monkeypatch.setattr(
        public_data, "Pm25ObservationRepository",
        lambda session: SimpleNamespace(
            get_latest_for_location=lambda location_id: SimpleNamespace(
                value_ug_m3=Decimal("62.4"), unit="ug/m3", observed_at=NOW,
                received_at=NOW,
            )
        ),
    )

    result = public_data.get_current_conditions(now=NOW)

    assert result.http_status_code == 200
    assert result.payload["status"] == "available"
    assert result.payload["pm25"]["value_ug_m3"] == Decimal("62.4")


def test_current_conditions_hides_stale_data(monkeypatch) -> None:
    configure_database(monkeypatch)
    monkeypatch.setattr(public_data, "get_settings", settings)
    monkeypatch.setattr(
        public_data, "MonitoringLocationRepository",
        lambda session: SimpleNamespace(
            get_by_provider_location_id=lambda provider, location_id: SimpleNamespace(
                id=LOCATION_ID, active=True, provider="openaq", name="New Delhi PM2.5 Station"
            )
        ),
    )
    monkeypatch.setattr(
        public_data, "Pm25ObservationRepository",
        lambda session: SimpleNamespace(
            get_latest_for_location=lambda location_id: SimpleNamespace(
                value_ug_m3=Decimal("62.4"), unit="ug/m3",
                observed_at=NOW - timedelta(hours=4), received_at=NOW,
            )
        ),
    )

    result = public_data.get_current_conditions(now=NOW)

    assert result.http_status_code == 503
    assert result.payload["code"] == "STALE_PM25_DATA"


def test_latest_forecasts_requires_complete_successful_run(monkeypatch) -> None:
    configure_database(monkeypatch)
    monkeypatch.setattr(
        public_data, "ForecastRunRepository",
        lambda session: SimpleNamespace(
            latest_succeeded=lambda: SimpleNamespace(
                id=RUN_ID, issued_at=NOW, model_version="airaware-operational-2026-08-31"
            )
        ),
    )
    monkeypatch.setattr(
        public_data, "ForecastRepository",
        lambda session: SimpleNamespace(list_for_run=lambda run_id: []),
    )

    result = public_data.get_latest_forecasts()

    assert result.http_status_code == 503
    assert result.payload["code"] == "FORECASTS_NOT_AVAILABLE"


def test_latest_forecasts_returns_all_three_saved_horizons(monkeypatch) -> None:
    configure_database(monkeypatch)
    monkeypatch.setattr(
        public_data, "ForecastRunRepository",
        lambda session: SimpleNamespace(
            latest_succeeded=lambda: SimpleNamespace(
                id=RUN_ID, issued_at=NOW, model_version="airaware-operational-2026-08-31"
            )
        ),
    )
    saved = [
        SimpleNamespace(
            horizon_hours=horizon, target_at=NOW + timedelta(hours=horizon),
            predicted_value_ug_m3=Decimal("60"), lower_bound_ug_m3=Decimal("40"),
            upper_bound_ug_m3=Decimal("80"),
        )
        for horizon in (1, 6, 24)
    ]
    monkeypatch.setattr(
        public_data, "ForecastRepository",
        lambda session: SimpleNamespace(list_for_run=lambda run_id: saved),
    )

    result = public_data.get_latest_forecasts()

    assert result.http_status_code == 200
    assert result.payload["status"] == "available"
    assert [item["horizon_hours"] for item in result.payload["forecasts"]] == [1, 6, 24]


def test_public_routes_return_safe_json(monkeypatch) -> None:
    monkeypatch.setattr(
        conditions_route,
        "get_current_conditions",
        lambda: PublicDataResult(503, {"status": "unavailable", "message": "Current conditions are temporarily unavailable.", "code": "DATABASE_UNAVAILABLE"}),
    )
    monkeypatch.setattr(
        forecasts_route,
        "get_latest_forecasts",
        lambda: PublicDataResult(503, {"status": "unavailable", "message": "Forecasts are not available yet.", "code": "FORECASTS_NOT_AVAILABLE"}),
    )

    current_response = client.get("/api/v1/current-conditions")
    forecast_response = client.get("/api/v1/forecasts/latest")

    assert current_response.status_code == 503
    assert current_response.json()["code"] == "DATABASE_UNAVAILABLE"
    assert forecast_response.status_code == 503
    assert forecast_response.json()["code"] == "FORECASTS_NOT_AVAILABLE"
