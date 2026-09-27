from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.api.routes import status as status_route
from backend.app.main import app
from backend.app.models.ingestion_run import IngestionRun
from backend.app.models.forecast_run import ForecastRun
from backend.app.services.status import build_public_status


client = TestClient(app)
NOW = datetime(2026, 9, 27, 10, tzinfo=timezone.utc)


def test_status_is_limited_before_ingestion_starts() -> None:
    result = build_public_status(database_connected=True)

    assert result.http_status_code == 200
    assert result.payload == {
        "status": "limited",
        "database": "connected",
        "pm25": {"status": "not_started", "last_completed_at": None},
        "weather": {"status": "not_started", "last_completed_at": None},
        "forecast": {"status": "not_started", "last_completed_at": None},
    }


def test_status_is_available_when_both_sources_succeed() -> None:
    pm25_run = IngestionRun(
        source_type="pm25",
        status="succeeded",
        completed_at=NOW,
    )
    weather_run = IngestionRun(
        source_type="weather",
        status="succeeded",
        completed_at=NOW,
    )
    forecast_run = ForecastRun(status="succeeded", issued_at=NOW, completed_at=NOW, model_version="test")

    result = build_public_status(
        database_connected=True,
        pm25_run=pm25_run,
        weather_run=weather_run,
        forecast_run=forecast_run,
    )

    assert result.http_status_code == 200
    assert result.payload["status"] == "available"
    assert result.payload["pm25"]["status"] == "available"
    assert result.payload["weather"]["status"] == "available"
    assert result.payload["forecast"]["status"] == "available"


def test_status_hides_failed_ingestion_reason() -> None:
    failed_run = IngestionRun(
        source_type="pm25",
        status="failed",
        completed_at=NOW,
        failure_reason="Provider token rejected: secret-value",
    )

    result = build_public_status(database_connected=True, pm25_run=failed_run)

    assert result.payload["status"] == "limited"
    assert result.payload["pm25"] == {
        "status": "unavailable",
        "last_completed_at": NOW,
    }
    assert "secret-value" not in str(result.payload)


def test_status_reports_unreachable_database() -> None:
    result = build_public_status(database_connected=False)

    assert result.http_status_code == 503
    assert result.payload["database"] == "unreachable"
    assert result.payload["pm25"]["status"] == "unavailable"


def test_status_endpoint_returns_safe_payload(monkeypatch) -> None:
    result = build_public_status(database_connected=False)
    monkeypatch.setattr(status_route, "get_public_status", lambda: result)

    response = client.get("/api/v1/status")

    assert response.status_code == 503
    assert response.json() == {
        "status": "limited",
        "database": "unreachable",
        "pm25": {"status": "unavailable", "last_completed_at": None},
        "weather": {"status": "unavailable", "last_completed_at": None},
        "forecast": {"status": "unavailable", "last_completed_at": None},
    }
