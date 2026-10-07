"""
Repositories Package.

Contains database access layer (repositories) for AirAware:
- MonitoringLocationRepository: Query monitored stations.
- PM25ObservationRepository: Upsert and fetch PM2.5 readings.
- WeatherRecordRepository: Upsert and fetch hourly weather data.
- ForecastRunRepository: Manage forecast execution metadata.
- ForecastRepository: Persist and retrieve 24-hour predictions with bounds.
- IngestionRunRepository: Log data ingestion jobs and outcomes.
- SystemEventRepository: Log system-level audit events and operational errors.
- AlertPreferenceRepository: Manage user-defined threshold preferences.
"""
