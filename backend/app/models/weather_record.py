"""Validated weather inputs for PM2.5 forecasting."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WeatherRecord(Base):
    """One approved weather record for a monitoring location and valid time."""

    __tablename__ = "weather_records"
    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "valid_at",
            name="uq_weather_records_location_valid_at",
        ),
        CheckConstraint(
            "humidity_percent >= 0 AND humidity_percent <= 100",
            name="ck_weather_records_humidity_range",
        ),
        CheckConstraint(
            "wind_speed_kmh >= 0",
            name="ck_weather_records_non_negative_wind_speed",
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
    valid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature_c: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    humidity_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    wind_speed_kmh: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
