"""Add monitoring locations.

Revision ID: 0001_add_monitoring_locations
Revises:
Create Date: 2026-09-27 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_add_monitoring_locations"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the monitoring_locations table."""
    op.create_table(
        "monitoring_locations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("provider_location_id", sa.String(length=100), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=8, scale=5), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=8, scale=5), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_monitoring_locations_latitude_range",
        ),
        sa.CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_monitoring_locations_longitude_range",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "provider_location_id",
            name="uq_monitoring_locations_provider_location",
        ),
    )


def downgrade() -> None:
    """Remove the monitoring_locations table."""
    op.drop_table("monitoring_locations")
