"""Anonymous browser-level PM2.5 alert preferences."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AlertPreference(Base):
    """A stored threshold preference; this does not send notifications."""

    __tablename__ = "alert_preferences"
    __table_args__ = (
        UniqueConstraint("browser_id", name="uq_alert_preferences_browser_id"),
        CheckConstraint(
            "threshold_ug_m3 > 0 AND threshold_ug_m3 <= 2000",
            name="ck_alert_preferences_threshold_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    browser_id: Mapped[UUID] = mapped_column(nullable=False)
    threshold_ug_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
