"""
Workers Package.

Contains automated background workers and operational scheduled tasks for AirAware:
- scheduler.py: Periodic worker loop executing ingestion and forecasting cycles.
- ingest.py: Automated pipeline fetching live PM2.5 and weather data from external providers.
- forecast.py: Automated execution of ML forecast generation, uncertainty bounds, and backfill.
"""
