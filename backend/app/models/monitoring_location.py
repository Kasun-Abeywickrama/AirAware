"""Monitoring location database model.

Represents an approved physical ambient air quality monitoring station
(e.g., Anand Lok in New Delhi) providing coordinates, timezone, and provider IDs.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MonitoringLocation(Base):
    """SQLAlchemy model for the 'monitoring_locations' table."""

    __tablename__ = "monitoring_locations"

    # Table-level constraints to ensure unique providers and valid GPS coordinates
    __table_args__ = (
        # Ensure only one record per station provider and provider location ID
        UniqueConstraint(
            "provider",
            "provider_location_id",
            name="uq_monitoring_locations_provider_location",
        ),
        # Latitude must be within valid geographic range [-90.0, 90.0]
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_monitoring_locations_latitude_range",
        ),
        # Longitude must be within valid geographic range [-180.0, 180.0]
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_monitoring_locations_longitude_range",
        ),
    )

    # Primary key: UUID v4
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Human-readable station name (e.g. 'Anand Lok, New Delhi')
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # External data provider name (e.g. 'openaq')
    provider: Mapped[str] = mapped_column(String(100), nullable=False)

    # Unique location identifier from the provider
    provider_location_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Station geographic coordinates
    latitude: Mapped[float] = mapped_column(Numeric(8, 5), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(8, 5), nullable=False)

    # Local IANA timezone name (e.g. 'Asia/Kolkata')
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    # Active status flag (defaults to True)
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
