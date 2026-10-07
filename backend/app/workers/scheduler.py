"""
Worker: Periodic Background Scheduler.

This module acts as the continuous operational daemon for AirAware:
- Periodically executes an ingestion run (fetching PM2.5 and meteorological observations).
- Followed by triggering the ML forecast pipeline.
- Handles unexpected exceptions safely without crashing the background daemon process.
"""

import logging
import time
from collections.abc import Callable

from ..config import Settings, get_settings
from .forecast import generate_forecasts
from .ingest import ingest_all


logger = logging.getLogger(__name__)


def run_cycle(settings: Settings | None = None) -> bool:
    """
    Execute one complete operational cycle:
    1. Ingest latest PM2.5 and Weather observations.
    2. Run ML models to produce fresh 1h, 6h, and 24h air quality forecasts.

    Args:
        settings: Application settings configuration.

    Returns:
        True if both ingestion and forecasting succeeded, False otherwise.
    """
    active_settings = settings or get_settings()

    # Step 1: External data ingestion
    ingestion_ok = ingest_all(active_settings)

    # Step 2: Machine learning forecast generation
    forecast_ok = generate_forecasts(active_settings)

    logger.info(
        "Operational worker cycle completed: ingestion_ok=%s forecast_ok=%s",
        ingestion_ok,
        forecast_ok,
    )
    return ingestion_ok and forecast_ok


def run_forever(
    settings: Settings | None = None,
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """
    Run continuous background daemon loop.

    Executes `run_cycle()` immediately at startup, then repeats at the configured
    interval (e.g. every 3600 seconds / 1 hour).
    Catches top-level exceptions to ensure the daemon continues running across transient network hiccups.

    Args:
        settings: Application settings configuration.
        sleep: Sleep function dependency injection (defaults to time.sleep).
    """
    active_settings = settings or get_settings()
    logger.info("Operational worker started with interval=%s seconds", active_settings.worker_interval_seconds)
    while True:
        try:
            run_cycle(active_settings)
        except Exception:
            # Prevent background worker from terminating due to unhandled provider errors
            logger.exception("Operational worker cycle stopped unexpectedly.")
        sleep(active_settings.worker_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
