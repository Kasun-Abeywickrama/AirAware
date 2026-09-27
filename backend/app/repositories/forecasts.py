"""Queries and inserts for saved PM2.5 forecasts."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.forecast import Forecast


class ForecastRepository:
    """Store forecast outputs after the full run has passed validation."""

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
        statement = (
            select(Forecast)
            .where(Forecast.forecast_run_id == forecast_run_id)
            .order_by(Forecast.horizon_hours)
        )
        return list(self._session.scalars(statement).all())
