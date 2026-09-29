"""Manual command to generate stored forecasts from validated live inputs."""

from datetime import datetime, timezone

from sqlalchemy import select

from ..config import Settings, get_settings
from ..database import get_session_factory
from ..models.pm25_observation import Pm25Observation
from ..models.weather_record import WeatherRecord
from ..repositories.forecast_runs import ForecastRunRepository
from ..repositories.forecasts import ForecastRepository
from ..repositories.monitoring_locations import MonitoringLocationRepository
from ..repositories.system_events import SystemEventRepository
from ..services.forecast_inputs import check_forecast_input_readiness
from ..services.forecasting import ForecastGenerationError, PackagedModelService


def generate_forecasts(settings: Settings | None = None) -> bool:
    """Generate the three forecast horizons, or record one safe failed run."""
    active_settings = settings or get_settings()
    session = get_session_factory()()
    issued_at = datetime.now(timezone.utc)
    run = None
    try:
        try:
            service = PackagedModelService(active_settings)
            model_version = service.model_version
        except ForecastGenerationError:
            service = None
            model_version = "unavailable"

        runs = ForecastRunRepository(session)
        events = SystemEventRepository(session)
        run = runs.start(issued_at=issued_at, model_version=model_version)
        location = MonitoringLocationRepository(session).get_by_provider_location_id(
            "openaq", str(active_settings.openaq_location_id)
        )
        if location is None or not location.active:
            raise ForecastGenerationError("Configured monitoring location is unavailable.")
        if service is None:
            raise ForecastGenerationError("Required forecast model files are unavailable.")

        readiness = check_forecast_input_readiness(
            session, location_id=location.id, settings=active_settings
        )
        if not readiness.ready or readiness.issue_at is None:
            raise ForecastGenerationError(readiness.reason or "Forecast inputs are unavailable.")

        forecasts, input_version = service.generate(
            pm25_records=list(
                session.scalars(
                    select(Pm25Observation).where(Pm25Observation.location_id == location.id)
                ).all()
            ),
            weather_records=list(
                session.scalars(
                    select(WeatherRecord).where(WeatherRecord.location_id == location.id)
                ).all()
            ),
            issue_at=readiness.issue_at,
        )
        repository = ForecastRepository(session)
        for forecast in forecasts:
            saved_forecast = repository.create(
                forecast_run_id=run.id,
                horizon_hours=forecast.horizon_hours,
                target_at=forecast.target_at,
                predicted_value_ug_m3=forecast.predicted_value_ug_m3,
                lower_bound_ug_m3=forecast.lower_bound_ug_m3,
                upper_bound_ug_m3=forecast.upper_bound_ug_m3,
            )
            repository.create_explanation(
                forecast_id=saved_forecast.id,
                method=forecast.explanation.method,
                baseline_value_ug_m3=forecast.explanation.baseline_value_ug_m3,
                completeness_error_ug_m3=forecast.explanation.completeness_error_ug_m3,
                factors=forecast.explanation.factors,
            )
        runs.mark_succeeded(run, input_version=input_version)
        events.record(component="forecast", level="info", message="Operational forecasts generated.")
        session.commit()
        return True
    except ForecastGenerationError as error:
        if run is None:
            session.rollback()
            return False
        ForecastRunRepository(session).mark_failed(run, str(error))
        SystemEventRepository(session).record(
            component="forecast", level="warning", message="Operational forecasts are unavailable."
        )
        session.commit()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(0 if generate_forecasts() else 1)
