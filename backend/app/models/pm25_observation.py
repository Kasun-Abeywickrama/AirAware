"""PM2.5 observation database model.

Stores approved ground-truth PM2.5 concentration measurements ingested from OpenAQ.
Includes constraints to guarantee non-negative values and deduplication.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Pm25Observation(Base):
    """SQLAlchemy model for the 'pm25_observations' table."""

    __tablename__ = "pm25_observations"

    # Table-level constraints
    __table_args__ = (
        # Prevent duplicate observations for the same location at the same timestamp
        UniqueConstraint(
            "location_id",
            "observed_at",
            name="uq_pm25_observations_location_observed_at",
        ),
        # Physical constraint: particulate concentration cannot be negative
        CheckConstraint(
            "value_ug_m3 >= 0",
            name="ck_pm25_observations_non_negative_value",
        ),
        # Ensure all stored values adhere to the standard micrograms per cubic meter unit
        CheckConstraint(
            "unit = 'ug/m3'",
            name="ck_pm25_observations_unit",
        ),
    )

    # Primary key: UUID v4
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key referencing the monitoring station (ON DELETE RESTRICT prevents accidental orphan data)
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("monitoring_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Foreign key referencing the ingestion batch run that collected this reading
    ingestion_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # UTC timestamp when the measurement was taken at the sensor
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Measured concentration in µg/m³ stored as high-precision Numeric(10, 2)
    value_ug_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Standardized unit string ('ug/m3')
    unit: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ug/m3",
        server_default="ug/m3",
    )

    # Server timestamp when this record was inserted into the database
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
