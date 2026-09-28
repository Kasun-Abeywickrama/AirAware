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
    pm25_history_hours: int
    model_artifact_directory: Path = PROJECT_ROOT / "backend" / "model_artifacts"
    worker_interval_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    """Read and validate required configuration once per process."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be configured.")

    pm25_history_hours = int(os.getenv("PM25_HISTORY_HOURS", "168"))
    if pm25_history_hours < 168:
        raise RuntimeError("PM25_HISTORY_HOURS must be at least 168 for the packaged models.")
    worker_interval_seconds = int(os.getenv("WORKER_INTERVAL_SECONDS", "3600"))
    if worker_interval_seconds < 60:
        raise RuntimeError("WORKER_INTERVAL_SECONDS must be at least 60.")

    configured_model_directory = Path(
        os.getenv("MODEL_ARTIFACT_DIRECTORY", "backend/model_artifacts")
    )
    model_artifact_directory = (
        configured_model_directory
        if configured_model_directory.is_absolute()
        else PROJECT_ROOT / configured_model_directory
    )

    return Settings(
        database_url=database_url,
        openaq_api_key=os.getenv("OPENAQ_API_KEY") or None,
        openaq_location_id=int(os.getenv("OPENAQ_LOCATION_ID", "6145551")),
        openaq_sensor_id=int(os.getenv("OPENAQ_SENSOR_ID", "14745878")),
        station_name=os.getenv("STATION_NAME", "Anand Lok, New Delhi"),
        station_latitude=float(os.getenv("STATION_LATITUDE", "28.5587")),
        station_longitude=float(os.getenv("STATION_LONGITUDE", "77.21886")),
        station_timezone=os.getenv("STATION_TIMEZONE", "Asia/Kolkata"),
        provider_timeout_seconds=float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "20")),
        maximum_observation_age_minutes=int(
            os.getenv("MAXIMUM_OBSERVATION_AGE_MINUTES", "180")
        ),
        pm25_history_hours=pm25_history_hours,
        model_artifact_directory=model_artifact_directory,
        worker_interval_seconds=worker_interval_seconds,
    )
