# AirAware – Class Diagram

## 1. Overview
The Class Diagram captures the **Domain and Data Access Layer** of AirAware. It models the SQLAlchemy ORM entities stored in PostgreSQL, their primary and foreign key constraints, data types, and multiplicities.

---

## 2. Mermaid Class Diagram

```mermaid
classDiagram
    direction TB

    class MonitoringLocation {
        +UUID id
        +String provider
        +String provider_location_id
        +String name
        +Decimal latitude
        +Decimal longitude
        +String timezone
        +DateTime created_at
        +DateTime updated_at
    }

    class Pm25Observation {
        +UUID id
        +UUID location_id
        +UUID ingestion_run_id
        +DateTime observed_at
        +Decimal value_ug_m3
        +String unit
        +String status
        +DateTime created_at
    }

    class WeatherRecord {
        +UUID id
        +UUID location_id
        +UUID ingestion_run_id
        +DateTime valid_at
        +Decimal temperature_c
        +Decimal humidity_percent
        +Decimal wind_speed_kmh
        +Decimal dew_point_c
        +Decimal surface_pressure_hpa
        +Decimal precipitation_mm
        +Decimal shortwave_radiation_w_m2
        +Decimal wind_direction_degrees
        +DateTime created_at
    }

    class ForecastRun {
        +UUID id
        +UUID location_id
        +DateTime issued_at
        +String model_version
        +String status
        +String failure_reason
        +DateTime created_at
    }

    class Forecast {
        +UUID id
        +UUID forecast_run_id
        +DateTime target_at
        +Integer horizon_hours
        +Decimal predicted_value_ug_m3
        +Decimal lower_bound_ug_m3
        +Decimal upper_bound_ug_m3
        +DateTime created_at
    }

    class ForecastExplanation {
        +UUID id
        +UUID forecast_id
        +String feature_name
        +Decimal importance_score
        +String summary_text
        +DateTime created_at
    }

    class IngestionRun {
        +UUID id
        +String source_type
        +String status
        +DateTime started_at
        +DateTime completed_at
        +String failure_reason
        +DateTime created_at
    }

    class SystemEvent {
        +UUID id
        +String component
        +String level
        +String message
        +DateTime created_at
    }

    class AlertPreference {
        +UUID id
        +String browser_id
        +Decimal threshold_pm25
        +Boolean active
        +DateTime created_at
        +DateTime updated_at
    }

    %% Relationships
    MonitoringLocation "1" --> "0..*" Pm25Observation : tracks
    MonitoringLocation "1" --> "0..*" WeatherRecord : records
    MonitoringLocation "1" --> "0..*" ForecastRun : targets

    IngestionRun "1" --> "0..*" Pm25Observation : audits
    IngestionRun "1" --> "0..*" WeatherRecord : audits

    ForecastRun "1" --> "1..*" Forecast : contains
    Forecast "1" --> "0..*" ForecastExplanation : explains
```

---

## 3. Entity Dictionary & Relationships

### Core Domain Entities
1. **`MonitoringLocation`**:
   - Represents the physical air monitoring station in New Delhi (e.g. Anand Lok or Central Delhi).
   - Serves as the spatial root for all observation and forecast records.
2. **`Pm25Observation`**:
   - Stores approved ground-truth PM2.5 readings ingested from OpenAQ.
   - Constrained by unique `(location_id, observed_at)` to prevent duplicate recordings.
3. **`WeatherRecord`**:
   - Stores synchronized hourly meteorological features ingested from Open-Meteo.
   - Constrained by unique `(location_id, valid_at)`.
4. **`ForecastRun`**:
   - Encapsulates a single ML execution cycle at a specific issue timestamp (`issued_at`).
   - Tracks the model version and whether the cycle succeeded or encountered validation issues.
5. **`Forecast`**:
   - Multi-horizon prediction points (e.g., +1h, +6h, +12h, +24h, +48h).
   - Contains point predictions alongside conformal prediction intervals (`lower_bound_ug_m3`, `upper_bound_ug_m3`).
6. **`ForecastExplanation`**:
   - Stores the top influential features (e.g. wind speed, diurnal cycle, 24-hour lag) and human-readable explanations.
7. **`IngestionRun` & `SystemEvent`**:
   - Provide complete operational auditability. Every provider call is tracked with start/completion times and failure diagnostics.
8. **`AlertPreference`**:
   - Stores client-side browser notification preferences and threshold values without requiring personal authentication.
