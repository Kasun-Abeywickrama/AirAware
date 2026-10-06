"""Add forecast run audit and forecast output tables.

Revision ID: 0007_add_forecasts
Revises: 0006_expand_weather_inputs
Create Date: 2026-09-28 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_add_forecasts"
down_revision: str | Sequence[str] | None = "0006_expand_weather_inputs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create traceable forecast storage."""
    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="running", nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("input_version", sa.String(length=64), nullable=True),
        sa.Column("failure_reason", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("status IN ('running', 'succeeded', 'failed')", name="ck_forecast_runs_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "forecasts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("forecast_run_id", sa.Uuid(), nullable=False),
        sa.Column("horizon_hours", sa.Integer(), nullable=False),
        sa.Column("target_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_value_ug_m3", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("lower_bound_ug_m3", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("upper_bound_ug_m3", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("horizon_hours IN (1, 6, 24)", name="ck_forecasts_supported_horizon"),
        sa.CheckConstraint("predicted_value_ug_m3 >= 0", name="ck_forecasts_non_negative_prediction"),
        sa.CheckConstraint("lower_bound_ug_m3 >= 0", name="ck_forecasts_non_negative_lower_bound"),
        sa.CheckConstraint("upper_bound_ug_m3 >= lower_bound_ug_m3", name="ck_forecasts_ordered_bounds"),
        sa.ForeignKeyConstraint(["forecast_run_id"], ["forecast_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("forecast_run_id", "horizon_hours", name="uq_forecasts_run_horizon"),
    )


def downgrade() -> None:
    """Remove forecast storage."""
    op.drop_table("forecasts")
    op.drop_table("forecast_runs")
