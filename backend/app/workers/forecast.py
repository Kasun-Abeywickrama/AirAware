"""Manual command to generate stored forecasts from validated live inputs."""

from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy import select

from ..config import Settings, get_settings
from ..database import get_session_factory
from ..models.forecast_run import ForecastRun
from ..models.pm25_observation import Pm25Observation
from ..models.weather_record import WeatherRecord
from ..repositories.forecast_runs import ForecastRunRepository
from ..repositories.forecasts import ForecastRepository
from ..repositories.monitoring_locations import MonitoringLocationRepository
from ..repositories.system_events import SystemEventRepository
from ..services.forecast_inputs import check_forecast_input_readiness, evaluate_forecast_input_records
from ..services.forecasting import ForecastGenerationError, PackagedModelService

logger = logging.getLogger(__name__)


def generate_forecasts(settings: Settings | None = None, backfill_recent: bool = True) -> bool:
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

        if backfill_recent and service is not None:
            _backfill_historical_forecasts(
                session=session,
                service=service,
                location=location,
                settings=active_settings,
                max_hours=24,
            )

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


def _backfill_historical_forecasts(
    session,
    service: PackagedModelService,
    location,
    settings: Settings,
    max_hours: int = 24,
) -> int:
    """Safely backfill missing hourly forecast runs from recent system downtime."""
    try:
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=max_hours)

        existing_runs = session.scalars(
            select(ForecastRun).where(
                ForecastRun.issued_at >= since,
                ForecastRun.status == "succeeded",
            )
        ).all()
        existing_hours = {
            r.issued_at.replace(minute=0, second=0, microsecond=0) for r in existing_runs
        }

        all_pm25 = list(
            session.scalars(
                select(Pm25Observation).where(Pm25Observation.location_id == location.id)
            ).all()
        )
        all_weather = list(
            session.scalars(
                select(WeatherRecord).where(WeatherRecord.location_id == location.id)
            ).all()
        )

        backfilled_count = 0
        repository = ForecastRepository(session)
        runs_repo = ForecastRunRepository(session)

        start_hour = since.replace(minute=0, second=0, microsecond=0)
        end_hour = now.replace(minute=0, second=0, microsecond=0)
        current_hour = start_hour

        while current_hour < end_hour:
            if current_hour not in existing_hours:
                historical_pm = [p for p in all_pm25 if p.observed_at <= current_hour]
                readiness = evaluate_forecast_input_records(
                    pm25_records=historical_pm,
                    weather_records=all_weather,
                    settings=settings,
                    now=current_hour,
                )
                if readiness.ready and readiness.issue_at is not None:
                    try:
                        backfill_run = runs_repo.start(
                            issued_at=current_hour, model_version=service.model_version
                        )
                        forecasts, input_ver = service.generate(
                            pm25_records=historical_pm,
                            weather_records=all_weather,
                            issue_at=readiness.issue_at,
                        )
                        for forecast in forecasts:
                            saved = repository.create(
                                forecast_run_id=backfill_run.id,
                                horizon_hours=forecast.horizon_hours,
                                target_at=forecast.target_at,
                                predicted_value_ug_m3=forecast.predicted_value_ug_m3,
                                lower_bound_ug_m3=forecast.lower_bound_ug_m3,
                                upper_bound_ug_m3=forecast.upper_bound_ug_m3,
                            )
                            repository.create_explanation(
                                forecast_id=saved.id,
                                method=forecast.explanation.method,
                                baseline_value_ug_m3=forecast.explanation.baseline_value_ug_m3,
                                completeness_error_ug_m3=forecast.explanation.completeness_error_ug_m3,
                                factors=forecast.explanation.factors,
                            )
                        runs_repo.mark_succeeded(backfill_run, input_version=input_ver)
                        session.commit()
                        backfilled_count += 1
                        existing_hours.add(current_hour)
                    except Exception as err:
                        logger.warning("Backfill failed for hour %s: %s", current_hour, err)
                        session.rollback()
            current_hour += timedelta(hours=1)

        if backfilled_count > 0:
            events = SystemEventRepository(session)
            events.record(
                component="forecast_backfill",
                level="info",
                message=f"Backfilled {backfilled_count} missing historical forecast runs.",
            )
            session.commit()
            logger.info("Backfilled %s missing forecast runs.", backfilled_count)
        return backfilled_count
    except Exception as err:
        logger.warning("Historical forecast backfilling encountered an error: %s", err)
        session.rollback()
        return 0


if __name__ == "__main__":
    raise SystemExit(0 if generate_forecasts() else 1)
