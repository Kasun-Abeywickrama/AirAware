from decimal import Decimal

import pytest

from backend.app import adapters
from backend.app.adapters import OpenAQAdapter, OpenMeteoAdapter, ProviderError
from backend.app.config import Settings


def settings(*, api_key: str | None = "test-key") -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused",
        openaq_api_key=api_key,
        openaq_location_id=8118,
        openaq_sensor_id=23534,
        station_name="New Delhi PM2.5 Station",
        station_latitude=28.63576,
        station_longitude=77.22445,
        station_timezone="Asia/Kolkata",
        provider_timeout_seconds=20,
        maximum_observation_age_minutes=180,
    )


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class FakeClient:
    def __init__(self, response: FakeResponse):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def get(self, url, **kwargs):
        return self.response


def test_openaq_adapter_normalizes_valid_pm25_reading(monkeypatch) -> None:
    response = FakeResponse(
        200,
        {
            "results": [
                {
                    "sensorsId": 23534,
                    "value": 62.4,
                    "datetime": {"utc": "2026-09-27T10:00:00Z"},
                    "parameter": {"units": "µg/m³"},
                }
            ]
        },
    )
    monkeypatch.setattr(adapters.httpx, "Client", lambda timeout: FakeClient(response))

    reading = OpenAQAdapter(settings()).latest_pm25()

    assert reading.value_ug_m3 == Decimal("62.4")
    assert reading.unit == "ug/m3"
    assert reading.observed_at.tzinfo is not None


@pytest.mark.parametrize(
    ("api_key", "status_code", "payload"),
    [
        (None, 200, {"results": []}),
        ("test-key", 503, {}),
        ("test-key", 200, {"results": []}),
    ],
)
def test_openaq_adapter_rejects_missing_or_unavailable_data(
    monkeypatch,
    api_key,
    status_code,
    payload,
) -> None:
    monkeypatch.setattr(
        adapters.httpx,
        "Client",
        lambda timeout: FakeClient(FakeResponse(status_code, payload)),
    )

    with pytest.raises(ProviderError):
        OpenAQAdapter(settings(api_key=api_key)).latest_pm25()


def test_open_meteo_adapter_returns_hourly_weather(monkeypatch) -> None:
    response = FakeResponse(
        200,
        {
            "hourly": {
                "time": ["2026-09-27T10:00", "2026-09-27T11:00"],
                "temperature_2m": [31.5, 32.0],
                "relative_humidity_2m": [72, 70],
                "wind_speed_10m": [10.2, 11.0],
            }
        },
    )
    monkeypatch.setattr(adapters.httpx, "Client", lambda timeout: FakeClient(response))

    readings = OpenMeteoAdapter(settings()).hourly_weather()

    assert len(readings) == 2
    assert readings[0].temperature_c == Decimal("31.5")
    assert readings[0].humidity_percent == Decimal("72")
    assert readings[0].wind_speed_kmh == Decimal("10.2")


def test_open_meteo_adapter_rejects_malformed_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        adapters.httpx,
        "Client",
        lambda timeout: FakeClient(FakeResponse(200, {"hourly": {"time": []}})),
    )

    with pytest.raises(ProviderError):
        OpenMeteoAdapter(settings()).hourly_weather()
