"""Add system events.

Revision ID: 0005_add_system_events
Revises: 0004_add_weather_records
Create Date: 2026-09-27 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_add_system_events"
down_revision: str | Sequence[str] | None = "0004_add_weather_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the system_events table."""
    op.create_table(
        "system_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("component", sa.String(length=100), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "level IN ('info', 'warning', 'error')",
            name="ck_system_events_level",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Remove the system_events table."""
    op.drop_table("system_events")
