"""Add anonymous alert preferences.

Revision ID: 0008_add_alert_preferences
Revises: 0007_add_forecasts
Create Date: 2026-09-28 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_add_alert_preferences"
down_revision: str | Sequence[str] | None = "0007_add_forecasts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create storage for a browser's saved PM2.5 threshold preference."""
    op.create_table(
        "alert_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("browser_id", sa.Uuid(), nullable=False),
        sa.Column("threshold_ug_m3", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("threshold_ug_m3 > 0 AND threshold_ug_m3 <= 2000", name="ck_alert_preferences_threshold_range"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("browser_id", name="uq_alert_preferences_browser_id"),
    )


def downgrade() -> None:
    """Remove anonymous alert preferences."""
    op.drop_table("alert_preferences")
