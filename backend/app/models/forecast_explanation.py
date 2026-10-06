"""Stored, user-facing explanations generated with each forecast."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ForecastExplanation(Base):
    """One validated grouped explanation for one saved forecast."""

    __tablename__ = "forecast_explanations"
    __table_args__ = (UniqueConstraint("forecast_id", name="uq_forecast_explanations_forecast"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    forecast_id: Mapped[UUID] = mapped_column(
        ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False
    )
    method: Mapped[str] = mapped_column(String(80), nullable=False)
    baseline_value_ug_m3: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    completeness_error_ug_m3: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    factors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
