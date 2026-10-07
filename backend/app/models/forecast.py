"""Forecast point database model.

Stores multi-horizon point predictions (+1h, +6h, +24h) along with
calibrated conformal prediction uncertainty bounds (lower and upper limits).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Forecast(Base):
    """SQLAlchemy model for the 'forecasts' table."""

    __tablename__ = "forecasts"

    # Integrity and physical constraints
    __table_args__ = (
        # Only one forecast per horizon per forecast run
        UniqueConstraint("forecast_run_id", "horizon_hours", name="uq_forecasts_run_horizon"),
        # Supported forecast horizons: +1 hour, +6 hours, +24 hours
        CheckConstraint("horizon_hours IN (1, 6, 24)", name="ck_forecasts_supported_horizon"),
        # PM2.5 prediction cannot be negative
        CheckConstraint("predicted_value_ug_m3 >= 0", name="ck_forecasts_non_negative_prediction"),
        # Conformal lower bound cannot be negative
        CheckConstraint("lower_bound_ug_m3 >= 0", name="ck_forecasts_non_negative_lower_bound"),
        # Upper bound must always be greater than or equal to the lower bound
        CheckConstraint("upper_bound_ug_m3 >= lower_bound_ug_m3", name="ck_forecasts_ordered_bounds"),
    )

    # Primary key: UUID v4
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key referencing parent forecast run
    forecast_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("forecast_runs.id", ondelete="RESTRICT"), nullable=False
    )

    # Prediction horizon in hours (+1, +6, or +24)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    # Target future UTC timestamp for which the prediction is made
    target_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Model point prediction in µg/m³
    predicted_value_ug_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Conformal prediction interval: calibrated lower bound in µg/m³
    lower_bound_ug_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Conformal prediction interval: calibrated upper bound in µg/m³
    upper_bound_ug_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
