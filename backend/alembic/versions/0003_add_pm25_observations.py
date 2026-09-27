"""Add PM2.5 observations.

Revision ID: 0003_add_pm25_observations
Revises: 0002_add_ingestion_runs
Create Date: 2026-09-27 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_add_pm25_observations"
down_revision: str | Sequence[str] | None = "0002_add_ingestion_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the pm25_observations table."""
    op.create_table(
        "pm25_observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("ingestion_run_id", sa.Uuid(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value_ug_m3", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=10), server_default="ug/m3", nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "value_ug_m3 >= 0",
            name="ck_pm25_observations_non_negative_value",
        ),
        sa.CheckConstraint(
            "unit = 'ug/m3'",
            name="ck_pm25_observations_unit",
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"],
            ["ingestion_runs.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["monitoring_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "location_id",
            "observed_at",
            name="uq_pm25_observations_location_observed_at",
        ),
    )


def downgrade() -> None:
    """Remove the pm25_observations table."""
    op.drop_table("pm25_observations")
