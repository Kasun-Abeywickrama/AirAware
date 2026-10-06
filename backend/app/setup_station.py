"""Manual command to create or update the configured monitoring station."""

from .config import get_settings
from .database import get_session_factory
from .repositories.monitoring_locations import MonitoringLocationRepository


def setup_configured_station() -> None:
    """Persist the configured OpenAQ station without inserting migration seed data."""
    session = get_session_factory()()
    try:
        MonitoringLocationRepository(session).upsert_configured_openaq_location(get_settings())
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    setup_configured_station()
