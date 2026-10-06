"""Add ingestion runs.

Revision ID: 0002_add_ingestion_runs
Revises: 0001_add_monitoring_locations
Create Date: 2026-09-27 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_add_ingestion_runs"
down_revision: str | Sequence[str] | None = "0001_add_monitoring_locations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the ingestion_runs table."""
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="running", nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_type IN ('pm25', 'weather')",
            name="ck_ingestion_runs_source_type",
        ),
        sa.CheckConstraint(
            "status IN ('running', 'succeeded', 'failed')",
            name="ck_ingestion_runs_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Remove the ingestion_runs table."""
    op.drop_table("ingestion_runs")
