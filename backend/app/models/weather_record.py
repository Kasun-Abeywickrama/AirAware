"""Weather record database model.

Stores hourly meteorological observations and forecasts ingested from Open-Meteo.
Provides key atmospheric features (temperature, humidity, wind, solar radiation)
used as dynamic inputs for machine learning PM2.5 forecasting models.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WeatherRecord(Base):
    """SQLAlchemy model for the 'weather_records' table."""

    __tablename__ = "weather_records"

    # Table-level physical constraints for atmospheric variables
    __table_args__ = (
        # Ensure only one weather entry per location for a specific valid timestamp
        UniqueConstraint(
            "location_id",
            "valid_at",
            name="uq_weather_records_location_valid_at",
        ),
        # Relative humidity percentage must be between 0% and 100%
        CheckConstraint(
            "humidity_percent >= 0 AND humidity_percent <= 100",
            name="ck_weather_records_humidity_range",
        ),
        # Wind speed cannot be negative
        CheckConstraint(
            "wind_speed_kmh >= 0",
            name="ck_weather_records_non_negative_wind_speed",
        ),
        # Precipitation cannot be negative
        CheckConstraint(
            "precipitation_mm IS NULL OR precipitation_mm >= 0",
            name="ck_weather_records_non_negative_precipitation",
        ),
        # Solar radiation cannot be negative
        CheckConstraint(
            "shortwave_radiation_w_m2 IS NULL OR shortwave_radiation_w_m2 >= 0",
            name="ck_weather_records_non_negative_radiation",
        ),
        # Atmospheric pressure must be strictly positive (> 0 hPa)
        CheckConstraint(
            "surface_pressure_hpa IS NULL OR surface_pressure_hpa > 0",
            name="ck_weather_records_positive_surface_pressure",
        ),
        # Wind compass direction must be between 0° and 360°
        CheckConstraint(
            "wind_direction_degrees IS NULL OR (wind_direction_degrees >= 0 AND wind_direction_degrees <= 360)",
            name="ck_weather_records_wind_direction_range",
        ),
    )

    # Primary key: UUID v4
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key referencing the monitoring location
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("monitoring_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Foreign key referencing the ingestion batch run
    ingestion_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # UTC timestamp for which these weather conditions apply
    valid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Core meteorological features used in ML models
    temperature_c: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)          # Air temperature in °C
    humidity_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)       # Relative humidity in %
    wind_speed_kmh: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)         # Wind speed in km/h
    dew_point_c: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)      # Dew point in °C
    surface_pressure_hpa: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True) # Pressure in hPa
    precipitation_mm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)      # Rainfall in mm
    shortwave_radiation_w_m2: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True) # Solar radiation in W/m²
    wind_direction_degrees: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)   # Compass angle (0-360°)

    # Server insertion timestamp
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
