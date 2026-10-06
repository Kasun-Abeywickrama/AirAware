from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from backend.app.config import Settings
from backend.app.models.forecast import Forecast
from backend.app.models.forecast_run import ForecastRun
from backend.app.models.pm25_observation import Pm25Observation
from backend.app.models.weather_record import WeatherRecord
from backend.app.repositories.forecast_runs import ForecastRunRepository
from backend.app.repositories.forecasts import ForecastRepository
from backend.app.services import forecasting
from backend.app.services.forecasting import PackagedModelService


LOCATION_ID = UUID("00000000-0000-0000-0000-000000000120")
RUN_ID = UUID("00000000-0000-0000-0000-000000000121")
ISSUE_AT = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)


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
    )


def input_records() -> tuple[list[Pm25Observation], list[WeatherRecord]]:
    pm25 = [
        Pm25Observation(
            location_id=LOCATION_ID,
            ingestion_run_id=RUN_ID,
            observed_at=ISSUE_AT - timedelta(hours=offset),
            value_ug_m3=Decimal("60"),
            unit="ug/m3",
        )
        for offset in range(169)
    ]
    weather = [
        WeatherRecord(
            location_id=LOCATION_ID,
            ingestion_run_id=RUN_ID,
            valid_at=ISSUE_AT - timedelta(hours=offset),
            temperature_c=Decimal("31"), humidity_percent=Decimal("72"),
            wind_speed_kmh=Decimal("10"), dew_point_c=Decimal("25"),
            surface_pressure_hpa=Decimal("1004"), precipitation_mm=Decimal("0"),
            shortwave_radiation_w_m2=Decimal("500"), wind_direction_degrees=Decimal("180"),
        )
        for offset in range(169)
    ]
    return pm25, weather


class FakeSession:
    def __init__(self):
        self.added = []
        self.flush_count = 0

    def add(self, item) -> None:
        self.added.append(item)

    def flush(self) -> None:
        self.flush_count += 1

    def scalar(self, statement):
        return None

    def scalars(self, statement):
        return type("Rows", (), {"all": lambda self: []})()


class FakeTree:
    def predict(self, values):
        return [100.0]


def fake_explanation(*args, **kwargs):
    return forecasting.GeneratedExplanation(
        method="test", baseline_value_ug_m3=Decimal("50"),
        completeness_error_ug_m3=Decimal("0"),
        factors=[],
    )


def test_forecast_schema_has_required_constraints() -> None:
    forecast_names = {constraint.name for constraint in Forecast.__table__.constraints}
    run_names = {constraint.name for constraint in ForecastRun.__table__.constraints}

    assert "ck_forecasts_supported_horizon" in forecast_names
    assert "ck_forecasts_ordered_bounds" in forecast_names
    assert "ck_forecast_runs_status" in run_names
    assert sum(isinstance(item, ForeignKeyConstraint) for item in Forecast.__table__.constraints) == 1
    assert sum(isinstance(item, UniqueConstraint) for item in Forecast.__table__.constraints) == 1
    assert sum(isinstance(item, CheckConstraint) for item in Forecast.__table__.constraints) == 4


def test_forecast_repositories_create_run_and_output() -> None:
    session = FakeSession()
    run = ForecastRunRepository(session).start(
        issued_at=ISSUE_AT, model_version="airaware-operational-2026-08-31"
    )
    run.id = RUN_ID
    forecast = ForecastRepository(session).create(
        forecast_run_id=RUN_ID, horizon_hours=1, target_at=ISSUE_AT + timedelta(hours=1),
        predicted_value_ug_m3=Decimal("60"), lower_bound_ug_m3=Decimal("40"),
        upper_bound_ug_m3=Decimal("80"),
    )

    assert run.status == "running"
    assert forecast.horizon_hours == 1
    assert session.flush_count == 2


def test_forecast_run_can_be_associated_with_location_id() -> None:
    session = FakeSession()
    run = ForecastRunRepository(session).start(
        issued_at=ISSUE_AT,
        model_version="airaware-operational-2026-08-31",
        location_id=LOCATION_ID,
    )
    assert run.location_id == LOCATION_ID


def test_packaged_model_service_generates_all_horizons(monkeypatch) -> None:
    service = PackagedModelService(settings())
    pm25, weather = input_records()
    weather = weather[:24]
    monkeypatch.setattr(service, "_verify_artifacts", lambda: None)
    monkeypatch.setattr(forecasting.joblib, "load", lambda path: FakeTree())
    monkeypatch.setattr(service, "_predict_gru", lambda filename, sequence: 80.0)
    monkeypatch.setattr(service, "_build_explanation", fake_explanation)

    forecasts, input_version = service.generate(
        pm25_records=pm25, weather_records=weather, issue_at=ISSUE_AT
    )

    assert [item.horizon_hours for item in forecasts] == [1, 6, 24]
    assert forecasts[0].predicted_value_ug_m3 == Decimal("85.00")
    assert forecasts[1].predicted_value_ug_m3 == Decimal("83.00")
    assert forecasts[2].predicted_value_ug_m3 == Decimal("100.00")
    assert all(item.upper_bound_ug_m3 >= item.lower_bound_ug_m3 for item in forecasts)
    assert len(input_version) == 64
    assert forecasts[0].explanation.method == "test"


def test_gru_pm25_history_is_grouped_by_its_actual_hour_lag() -> None:
    values = np.zeros((24, 14), dtype=float)
    values[:, 0] = 1

    grouped = forecasting._group_sequence_contributions(
        ["pm25", *[f"feature_{index}" for index in range(13)]], values
    )

    assert grouped["current_pm25"] == 1
    assert grouped["recent_pm25"] == 6
    assert grouped["older_pm25"] == 17


@pytest.mark.skipif(
    not Path(__file__).resolve().parents[1].joinpath("model_artifacts", "24h_tree.joblib").exists(),
    reason="Local model artifacts are intentionally not committed to Git.",
)
def test_verified_local_artifacts_generate_real_forecasts() -> None:
    pm25, weather = input_records()

    forecasts, input_version = PackagedModelService(settings()).generate(
        pm25_records=pm25, weather_records=weather, issue_at=ISSUE_AT
    )

    assert [item.horizon_hours for item in forecasts] == [1, 6, 24]
    assert all(item.predicted_value_ug_m3 >= 0 for item in forecasts)
    assert len(input_version) == 64
