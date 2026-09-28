"""Simple hourly operational worker for local Docker deployment."""

import logging
import time
from collections.abc import Callable

from ..config import Settings, get_settings
from .forecast import generate_forecasts
from .ingest import ingest_all


logger = logging.getLogger(__name__)


def run_cycle(settings: Settings | None = None) -> bool:
    """Run one ingestion attempt followed by one guarded forecast attempt."""
    active_settings = settings or get_settings()
    ingestion_ok = ingest_all(active_settings)
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
    """Run immediately at startup, then repeat at the configured interval."""
    active_settings = settings or get_settings()
    logger.info("Operational worker started with interval=%s seconds", active_settings.worker_interval_seconds)
    while True:
        try:
            run_cycle(active_settings)
        except Exception:
            # Keep a long-running worker alive. Detailed provider and forecast
            # outcomes are already recorded safely by their individual workflows.
            logger.exception("Operational worker cycle stopped unexpectedly.")
        sleep(active_settings.worker_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
