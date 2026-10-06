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
        CheckConstraint(
            "precipitation_mm IS NULL OR precipitation_mm >= 0",
            name="ck_weather_records_non_negative_precipitation",
        ),
        CheckConstraint(
            "shortwave_radiation_w_m2 IS NULL OR shortwave_radiation_w_m2 >= 0",
            name="ck_weather_records_non_negative_radiation",
        ),
        CheckConstraint(
            "surface_pressure_hpa IS NULL OR surface_pressure_hpa > 0",
            name="ck_weather_records_positive_surface_pressure",
        ),
        CheckConstraint(
            "wind_direction_degrees IS NULL OR (wind_direction_degrees >= 0 AND wind_direction_degrees <= 360)",
            name="ck_weather_records_wind_direction_range",
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
    # These columns are nullable only to preserve pre-0006 records. New provider
    # inputs are validated as a complete model-compatible weather record.
    dew_point_c: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    surface_pressure_hpa: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    precipitation_mm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    shortwave_radiation_w_m2: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    wind_direction_degrees: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
