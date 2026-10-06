"""Add location_id foreign key to forecast_runs.

Revision ID: 0010_forecast_runs_location
Revises: 0009_add_forecast_explanations
Create Date: 2026-10-06 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010_forecast_runs_location"
down_revision: str | Sequence[str] | None = "0009_add_forecast_explanations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add optional location_id referencing monitoring_locations."""
    op.add_column("forecast_runs", sa.Column("location_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_forecast_runs_location_id",
        "forecast_runs",
        "monitoring_locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove location_id from forecast_runs."""
    op.drop_constraint("fk_forecast_runs_location_id", "forecast_runs", type_="foreignkey")
    op.drop_column("forecast_runs", "location_id")
