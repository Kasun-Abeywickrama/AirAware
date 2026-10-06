"""Expand weather records for the packaged operational forecast models.

Revision ID: 0006_expand_weather_inputs
Revises: 0005_add_system_events
Create Date: 2026-09-27 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_expand_weather_inputs"
down_revision: str | Sequence[str] | None = "0005_add_system_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add weather variables used by the existing operational model artifacts."""
    op.add_column("weather_records", sa.Column("dew_point_c", sa.Numeric(precision=6, scale=2), nullable=True))
    op.add_column("weather_records", sa.Column("surface_pressure_hpa", sa.Numeric(precision=7, scale=2), nullable=True))
    op.add_column("weather_records", sa.Column("precipitation_mm", sa.Numeric(precision=7, scale=2), nullable=True))
    op.add_column("weather_records", sa.Column("shortwave_radiation_w_m2", sa.Numeric(precision=8, scale=2), nullable=True))
    op.add_column("weather_records", sa.Column("wind_direction_degrees", sa.Numeric(precision=6, scale=2), nullable=True))
    op.create_check_constraint(
        "ck_weather_records_non_negative_precipitation",
        "weather_records",
        "precipitation_mm IS NULL OR precipitation_mm >= 0",
    )
    op.create_check_constraint(
        "ck_weather_records_non_negative_radiation",
        "weather_records",
        "shortwave_radiation_w_m2 IS NULL OR shortwave_radiation_w_m2 >= 0",
    )
    op.create_check_constraint(
        "ck_weather_records_positive_surface_pressure",
        "weather_records",
        "surface_pressure_hpa IS NULL OR surface_pressure_hpa > 0",
    )
    op.create_check_constraint(
        "ck_weather_records_wind_direction_range",
        "weather_records",
        "wind_direction_degrees IS NULL OR (wind_direction_degrees >= 0 AND wind_direction_degrees <= 360)",
    )


def downgrade() -> None:
    """Remove the added forecast-input weather columns."""
    op.drop_constraint("ck_weather_records_wind_direction_range", "weather_records", type_="check")
    op.drop_constraint("ck_weather_records_positive_surface_pressure", "weather_records", type_="check")
    op.drop_constraint("ck_weather_records_non_negative_radiation", "weather_records", type_="check")
    op.drop_constraint("ck_weather_records_non_negative_precipitation", "weather_records", type_="check")
    op.drop_column("weather_records", "wind_direction_degrees")
    op.drop_column("weather_records", "shortwave_radiation_w_m2")
    op.drop_column("weather_records", "precipitation_mm")
    op.drop_column("weather_records", "surface_pressure_hpa")
    op.drop_column("weather_records", "dew_point_c")
