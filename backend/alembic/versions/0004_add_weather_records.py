"""Add weather records.

Revision ID: 0004_add_weather_records
Revises: 0003_add_pm25_observations
Create Date: 2026-09-27 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_add_weather_records"
down_revision: str | Sequence[str] | None = "0003_add_pm25_observations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the weather_records table."""
    op.create_table(
        "weather_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("ingestion_run_id", sa.Uuid(), nullable=False),
        sa.Column("valid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("humidity_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("wind_speed_kmh", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "humidity_percent >= 0 AND humidity_percent <= 100",
            name="ck_weather_records_humidity_range",
        ),
        sa.CheckConstraint(
            "wind_speed_kmh >= 0",
            name="ck_weather_records_non_negative_wind_speed",
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
            "valid_at",
            name="uq_weather_records_location_valid_at",
        ),
    )


def downgrade() -> None:
    """Remove the weather_records table."""
    op.drop_table("weather_records")
