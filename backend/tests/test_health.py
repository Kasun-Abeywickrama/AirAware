from fastapi.testclient import TestClient

from backend.app import database
from backend.app.main import app


client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_check_returns_connected(monkeypatch) -> None:
    monkeypatch.setattr(database, "check_database_connection", lambda: True)

    response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_database_health_check_hides_connection_error(monkeypatch) -> None:
    monkeypatch.setattr(database, "check_database_connection", lambda: False)

    response = client.get("/health/database")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unreachable"}
