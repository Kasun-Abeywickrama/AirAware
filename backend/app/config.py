"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Configuration needed by the backend foundation."""

    database_url: str
    openaq_api_key: str | None
    openaq_location_id: int
    openaq_sensor_id: int
    station_name: str
    station_latitude: float
    station_longitude: float
    station_timezone: str
    provider_timeout_seconds: float
    maximum_observation_age_minutes: int


@lru_cache
def get_settings() -> Settings:
    """Read and validate required configuration once per process."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be configured.")

    return Settings(
        database_url=database_url,
        openaq_api_key=os.getenv("OPENAQ_API_KEY") or None,
        openaq_location_id=int(os.getenv("OPENAQ_LOCATION_ID", "8118")),
        openaq_sensor_id=int(os.getenv("OPENAQ_SENSOR_ID", "23534")),
        station_name=os.getenv("STATION_NAME", "New Delhi PM2.5 Station"),
        station_latitude=float(os.getenv("STATION_LATITUDE", "28.63576")),
        station_longitude=float(os.getenv("STATION_LONGITUDE", "77.22445")),
        station_timezone=os.getenv("STATION_TIMEZONE", "Asia/Kolkata"),
        provider_timeout_seconds=float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "20")),
        maximum_observation_age_minutes=int(
            os.getenv("MAXIMUM_OBSERVATION_AGE_MINUTES", "180")
        ),
    )
