"""Approved PM2.5 monitoring locations."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MonitoringLocation(Base):
    """A verified monitoring station available for future data ingestion."""

    __tablename__ = "monitoring_locations"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_location_id",
            name="uq_monitoring_locations_provider_location",
        ),
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_monitoring_locations_latitude_range",
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_monitoring_locations_longitude_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_location_id: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(8, 5), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(8, 5), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
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
