"""Database bootstrap script for monitoring station setup.

Ensures the configured OpenAQ monitoring station (Anand Lok, New Delhi)
exists in the PostgreSQL database before ingestion or forecasting runs.
"""

from .config import get_settings
from .database import get_session_factory
from .repositories.monitoring_locations import MonitoringLocationRepository


def setup_configured_station() -> None:
    """Insert or update the configured OpenAQ station record in the database.

    Creates an active record for the monitoring location with its coordinates,
    timezone, and provider identifiers without requiring seed migrations.
    """
    session = get_session_factory()()
    try:
        MonitoringLocationRepository(session).upsert_configured_openaq_location(get_settings())
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    setup_configured_station()
