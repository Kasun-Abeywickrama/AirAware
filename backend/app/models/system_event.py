"""Safe operational events for system monitoring."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SystemEvent(Base):
    """A concise, safe event describing application behaviour."""

    __tablename__ = "system_events"
    __table_args__ = (
        CheckConstraint(
            "level IN ('info', 'warning', 'error')",
            name="ck_system_events_level",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    component: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
