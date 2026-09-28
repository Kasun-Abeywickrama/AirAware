from backend.app.config import Settings
from backend.app.workers import scheduler


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
        worker_interval_seconds=3600,
    )


def test_scheduler_cycle_runs_ingestion_then_forecasting(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(scheduler, "ingest_all", lambda active_settings: calls.append("ingest") or True)
    monkeypatch.setattr(
        scheduler, "generate_forecasts", lambda active_settings: calls.append("forecast") or True
    )

    assert scheduler.run_cycle(settings()) is True
    assert calls == ["ingest", "forecast"]


def test_scheduler_continues_after_a_failed_cycle(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(scheduler, "run_cycle", lambda active_settings: calls.append("cycle") or False)

    def stop_after_first_sleep(seconds: float) -> None:
        assert seconds == 3600
        raise KeyboardInterrupt

    try:
        scheduler.run_forever(settings(), sleep=stop_after_first_sleep)
    except KeyboardInterrupt:
        pass

    assert calls == ["cycle"]
