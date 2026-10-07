"""System event logging database model.

Stores structured telemetry and operational logs (info, warning, error)
for monitoring background pipeline health and diagnostic auditability.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SystemEvent(Base):
    """SQLAlchemy model for the 'system_events' table."""

    __tablename__ = "system_events"

    # Ensure log level matches standard logging severity levels
    __table_args__ = (
        CheckConstraint(
            "level IN ('info', 'warning', 'error')",
            name="ck_system_events_level",
        ),
    )

    # Primary key: UUID v4
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Subsystem or service name generating the event (e.g., 'ingest', 'forecast', 'scheduler')
    component: Mapped[str] = mapped_column(String(100), nullable=False)

    # Severity level: 'info', 'warning', or 'error'
    level: Mapped[str] = mapped_column(String(20), nullable=False)

    # Safe diagnostic log message
    message: Mapped[str] = mapped_column(String(500), nullable=False)

    # Event creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
