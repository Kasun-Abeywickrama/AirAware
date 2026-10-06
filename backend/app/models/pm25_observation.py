"""Validated PM2.5 measurements."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Pm25Observation(Base):
    """One approved PM2.5 measurement from an approved monitoring location."""

    __tablename__ = "pm25_observations"
    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "observed_at",
            name="uq_pm25_observations_location_observed_at",
        ),
        CheckConstraint(
            "value_ug_m3 >= 0",
            name="ck_pm25_observations_non_negative_value",
        ),
        CheckConstraint(
            "unit = 'ug/m3'",
            name="ck_pm25_observations_unit",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("monitoring_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ingestion_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value_ug_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ug/m3",
        server_default="ug/m3",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
