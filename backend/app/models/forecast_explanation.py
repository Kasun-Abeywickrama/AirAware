"""Forecast explanation database model.

Stores Explainable AI (XAI) feature attribution metadata for saved predictions,
including the baseline expected value, feature contributions, and attribution error.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ForecastExplanation(Base):
    """SQLAlchemy model for the 'forecast_explanations' table."""

    __tablename__ = "forecast_explanations"

    # Enforce 1-to-1 relationship between a Forecast and its ForecastExplanation
    __table_args__ = (UniqueConstraint("forecast_id", name="uq_forecast_explanations_forecast"),)

    # Primary key: UUID v4
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key referencing the forecast (CASCADE deletes explanation if forecast is removed)
    forecast_id: Mapped[UUID] = mapped_column(
        ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False
    )

    # Explanation algorithm method name (e.g., 'tree_shap' or 'feature_attribution')
    method: Mapped[str] = mapped_column(String(80), nullable=False)

    # Model baseline expected value (mean training output) in µg/m³
    baseline_value_ug_m3: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Numerical difference between (baseline + sum of contributions) and the model output
    completeness_error_ug_m3: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)

    # List of grouped feature impacts with contribution scores and user-friendly explanations
    factors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)

    # Database creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
