"""Forecast run audit database model.

Tracks each operational machine learning forecast execution cycle,
including start/completion timestamps, model versions, input checksums,
and failure diagnostics if errors occur.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ForecastRun(Base):
    """SQLAlchemy model for the 'forecast_runs' table."""

    __tablename__ = "forecast_runs"

    # Ensure status conforms to standardized state enum
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed')",
            name="ck_forecast_runs_status",
        ),
    )

    # Primary key: UUID v4
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key referencing the target monitoring station
    location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("monitoring_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Current execution status ('running', 'succeeded', or 'failed')
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running", server_default="running"
    )

    # Timestamp representing the forecast issue origin time
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Timestamp when model inference completed
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Version tag / identifier of the packaged ML model ensemble
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)

    # Hash / signature of input history vectors used for reproducibility
    input_version: Mapped[str | None] = mapped_column(String(64))

    # Safe error summary if forecast generation failed
    failure_reason: Mapped[str | None] = mapped_column(String(1000))

    # Database insertion timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
