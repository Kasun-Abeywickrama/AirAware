"""Repository for saving and querying PM2.5 forecasts and XAI explanations.

Handles forecast horizon persistence (+1h, +6h, +24h), conformal intervals,
feature importance attributions, and time-range queries for dashboards and planners.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.forecast import Forecast
from ..models.forecast_explanation import ForecastExplanation
from ..models.forecast_run import ForecastRun


class ForecastRepository:
    """Data access layer for the 'forecasts' and 'forecast_explanations' tables."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        forecast_run_id: UUID,
        horizon_hours: int,
        target_at: datetime,
        predicted_value_ug_m3: Decimal,
        lower_bound_ug_m3: Decimal,
        upper_bound_ug_m3: Decimal,
    ) -> Forecast:
        """Insert a single horizon forecast point with conformal uncertainty intervals."""
        forecast = Forecast(
            forecast_run_id=forecast_run_id,
            horizon_hours=horizon_hours,
            target_at=target_at,
            predicted_value_ug_m3=predicted_value_ug_m3,
            lower_bound_ug_m3=lower_bound_ug_m3,
            upper_bound_ug_m3=upper_bound_ug_m3,
        )
        self._session.add(forecast)
        self._session.flush()
        return forecast

    def list_for_run(self, forecast_run_id: UUID) -> list[Forecast]:
        """Fetch all horizon forecasts (+1h, +6h, +24h) belonging to a specific run."""
        statement = (
            select(Forecast)
            .where(Forecast.forecast_run_id == forecast_run_id)
            .order_by(Forecast.horizon_hours)
        )
        return list(self._session.scalars(statement).all())

    def create_explanation(
        self,
        *,
        forecast_id: UUID,
        method: str,
        baseline_value_ug_m3: Decimal,
        completeness_error_ug_m3: Decimal,
        factors: list[dict],
    ) -> ForecastExplanation:
        """Insert Explainable AI (XAI) feature importance factors for a forecast point."""
        explanation = ForecastExplanation(
            forecast_id=forecast_id,
            method=method,
            baseline_value_ug_m3=baseline_value_ug_m3,
            completeness_error_ug_m3=completeness_error_ug_m3,
            factors=factors,
        )
        self._session.add(explanation)
        self._session.flush()
        return explanation

    def explanations_for_forecasts(self, forecast_ids: list[UUID]) -> dict[UUID, ForecastExplanation]:
        """Fetch explanations in a single batch query, returned as a dictionary keyed by forecast_id."""
        if not forecast_ids:
            return {}
        statement = select(ForecastExplanation).where(ForecastExplanation.forecast_id.in_(forecast_ids))
        return {item.forecast_id: item for item in self._session.scalars(statement).all()}

    def list_since(
        self, since: datetime, location_id: UUID | None = None
    ) -> list[tuple[Forecast, ForecastRun]]:
        """Fetch chronological forecasts generated since a specific timestamp for history charts."""
        statement = (
            select(Forecast, ForecastRun)
            .join(ForecastRun, Forecast.forecast_run_id == ForecastRun.id)
            .where(Forecast.target_at >= since, ForecastRun.status == "succeeded")
        )
        if location_id is not None:
            statement = statement.where(ForecastRun.location_id == location_id)
        statement = statement.order_by(Forecast.target_at, ForecastRun.issued_at.desc())
        results = list(self._session.execute(statement).all())
        # Fallback query for runs generated before location_id was populated
        if not results and location_id is not None:
            fallback_stmt = (
                select(Forecast, ForecastRun)
                .join(ForecastRun, Forecast.forecast_run_id == ForecastRun.id)
                .where(
                    Forecast.target_at >= since,
                    ForecastRun.status == "succeeded",
                    ForecastRun.location_id.is_(None),
                )
                .order_by(Forecast.target_at, ForecastRun.issued_at.desc())
            )
            return list(self._session.execute(fallback_stmt).all())
        return results

    def list_for_target_range(
        self, *, start_at: datetime, end_at: datetime, location_id: UUID | None = None
    ) -> list[tuple[Forecast, ForecastRun]]:
        """Fetch successful forecasts whose target time falls within [start_at, end_at).

        Used by the Activity Planner to find candidate windows across a target day.
        """
        statement = (
            select(Forecast, ForecastRun)
            .join(ForecastRun, Forecast.forecast_run_id == ForecastRun.id)
            .where(
                Forecast.target_at >= start_at,
                Forecast.target_at < end_at,
                ForecastRun.status == "succeeded",
            )
        )
        if location_id is not None:
            statement = statement.where(ForecastRun.location_id == location_id)
        statement = statement.order_by(Forecast.target_at, ForecastRun.issued_at.desc())
        results = list(self._session.execute(statement).all())
        if not results and location_id is not None:
            fallback_stmt = (
                select(Forecast, ForecastRun)
                .join(ForecastRun, Forecast.forecast_run_id == ForecastRun.id)
                .where(
                    Forecast.target_at >= start_at,
                    Forecast.target_at < end_at,
                    ForecastRun.status == "succeeded",
                    ForecastRun.location_id.is_(None),
                )
                .order_by(Forecast.target_at, ForecastRun.issued_at.desc())
            )
            return list(self._session.execute(fallback_stmt).all())
        return results
