"""Store grouped XAI explanations alongside each saved forecast.

Revision ID: 0009_add_forecast_explanations
Revises: 0008_add_alert_preferences
Create Date: 2026-09-29 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009_add_forecast_explanations"
down_revision: str | Sequence[str] | None = "0008_add_alert_preferences"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create one explanation record for each saved forecast."""
    op.create_table(
        "forecast_explanations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("forecast_id", sa.Uuid(), nullable=False),
        sa.Column("method", sa.String(length=80), nullable=False),
        sa.Column("baseline_value_ug_m3", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("completeness_error_ug_m3", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("factors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("forecast_id", name="uq_forecast_explanations_forecast"),
    )


def downgrade() -> None:
    """Remove saved explanations."""
    op.drop_table("forecast_explanations")
