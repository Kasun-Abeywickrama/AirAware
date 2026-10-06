"""Audit records for PM2.5 and weather data collection."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class IngestionRun(Base):
    """One attempt to collect PM2.5 or weather data."""

    __tablename__ = "ingestion_runs"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('pm25', 'weather')",
            name="ck_ingestion_runs_source_type",
        ),
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed')",
            name="ck_ingestion_runs_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="running",
        server_default="running",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
