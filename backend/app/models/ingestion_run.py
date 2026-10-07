"""Ingestion run audit database model.

Tracks automated data collection attempts for both PM2.5 (OpenAQ)
and meteorological records (Open-Meteo), logging execution status and error diagnostics.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class IngestionRun(Base):
    """SQLAlchemy model for the 'ingestion_runs' table."""

    __tablename__ = "ingestion_runs"

    # Constraints to ensure valid source types and execution states
    __table_args__ = (
        # Allowed data sources: 'pm25' (OpenAQ) or 'weather' (Open-Meteo)
        CheckConstraint(
            "source_type IN ('pm25', 'weather')",
            name="ck_ingestion_runs_source_type",
        ),
        # Allowed execution states
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed')",
            name="ck_ingestion_runs_status",
        ),
    )

    # Primary key: UUID v4
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Type of data being ingested ('pm25' or 'weather')
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Status of the ingestion job ('running', 'succeeded', 'failed')
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="running",
        server_default="running",
    )

    # Timestamp when this ingestion cycle began
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Timestamp when this ingestion cycle completed (null while running)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Error message if the ingestion job failed
    failure_reason: Mapped[str | None] = mapped_column(String(1000))

    # Record insertion timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
