"""Database models for AirAware."""

from .ingestion_run import IngestionRun
from .monitoring_location import MonitoringLocation

__all__ = ["IngestionRun", "MonitoringLocation"]
