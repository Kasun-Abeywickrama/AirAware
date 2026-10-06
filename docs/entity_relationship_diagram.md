# AirAware – Entity Relationship Diagram (ERD)

## 1. Overview
The **Entity Relationship Diagram (ERD)** models the physical relational database schema of **AirAware** hosted in **PostgreSQL 17**. 

It details all table schemas, primary keys (`PK`), foreign keys (`FK`), unique constraints (`UQ`), check constraints (`CK`), data types, and cardinality notations (Crow's Foot notation).

---

## 2. Mermaid ER Diagram

```mermaid
erDiagram
    MONITORING_LOCATIONS {
        uuid id PK
        string name "VARCHAR(200)"
        string provider "VARCHAR(100)"
        string provider_location_id "VARCHAR(100)"
        numeric latitude "NUMERIC(8,5)"
        numeric longitude "NUMERIC(8,5)"
        string timezone "VARCHAR(64)"
        boolean active "DEFAULT true"
        timestamptz created_at
        timestamptz updated_at
    }

    INGESTION_RUNS {
        uuid id PK
        string source_type "VARCHAR(20) - pm25, weather"
        string status "VARCHAR(20) - running, succeeded, failed"
        timestamptz started_at
        timestamptz completed_at
        string failure_reason "VARCHAR(1000)"
        timestamptz created_at
    }

    PM25_OBSERVATIONS {
        uuid id PK
        uuid location_id FK
        uuid ingestion_run_id FK
        timestamptz observed_at
        numeric value_ug_m3 "NUMERIC(10,2) >= 0"
        string unit "VARCHAR(10) - ug/m3"
        timestamptz received_at
    }

    WEATHER_RECORDS {
        uuid id PK
        uuid location_id FK
        uuid ingestion_run_id FK
        timestamptz valid_at
        numeric temperature_c "NUMERIC(6,2)"
        numeric humidity_percent "NUMERIC(5,2) 0-100"
        numeric wind_speed_kmh "NUMERIC(7,2) >= 0"
        numeric dew_point_c "NUMERIC(6,2)"
        numeric surface_pressure_hpa "NUMERIC(7,2) > 0"
        numeric precipitation_mm "NUMERIC(7,2) >= 0"
        numeric shortwave_radiation_w_m2 "NUMERIC(8,2) >= 0"
        numeric wind_direction_degrees "NUMERIC(6,2) 0-360"
        timestamptz received_at
    }

    FORECAST_RUNS {
        uuid id PK
        string status "VARCHAR(20) - running, succeeded, failed"
        timestamptz issued_at
        timestamptz completed_at
        string model_version "VARCHAR(100)"
        string input_version "VARCHAR(64)"
        string failure_reason "VARCHAR(1000)"
        timestamptz created_at
    }

    FORECASTS {
        uuid id PK
        uuid forecast_run_id FK
        integer horizon_hours "IN (1, 6, 24)"
        timestamptz target_at
        numeric predicted_value_ug_m3 "NUMERIC(10,2) >= 0"
        numeric lower_bound_ug_m3 "NUMERIC(10,2) >= 0"
        numeric upper_bound_ug_m3 "NUMERIC(10,2) >= lower"
    }

    FORECAST_EXPLANATIONS {
        uuid id PK
        uuid forecast_id FK "UQ"
        string method "VARCHAR(80)"
        numeric baseline_value_ug_m3 "NUMERIC(10,2)"
        numeric completeness_error_ug_m3 "NUMERIC(10,4)"
        json factors "Top influential drivers"
        timestamptz created_at
    }

    ALERT_PREFERENCES {
        uuid id PK
        uuid browser_id "UQ"
        numeric threshold_ug_m3 "NUMERIC(10,2) 0-2000"
        boolean enabled "DEFAULT true"
        timestamptz updated_at
    }

    SYSTEM_EVENTS {
        uuid id PK
        string component "VARCHAR(100)"
        string level "VARCHAR(20) - info, warning, error"
        string message "VARCHAR(500)"
        timestamptz created_at
    }

    %% Relationships & Cardinalities
    MONITORING_LOCATIONS ||--o{ PM25_OBSERVATIONS : "monitors"
    MONITORING_LOCATIONS ||--o{ WEATHER_RECORDS : "records"

    INGESTION_RUNS ||--o{ PM25_OBSERVATIONS : "collects"
    INGESTION_RUNS ||--o{ WEATHER_RECORDS : "collects"

    FORECAST_RUNS ||--|{ FORECASTS : "generates"
    FORECASTS ||--o| FORECAST_EXPLANATIONS : "explained_by"
```

---

## 3. Database Schema Dictionary & Constraints

### 1. `monitoring_locations`
- **Primary Key**: `id (UUID)`
- **Unique Constraint**: `uq_monitoring_locations_provider_location (provider, provider_location_id)`
- **Check Constraints**:
  - `ck_monitoring_locations_latitude_range`: `-90 <= latitude <= 90`
  - `ck_monitoring_locations_longitude_range`: `-180 <= longitude <= 180`
- **Description**: Stores spatial stations (e.g., OpenAQ Anand Lok or Central Delhi).

### 2. `pm25_observations`
- **Primary Key**: `id (UUID)`
- **Foreign Keys**:
  - `location_id` $\rightarrow$ `monitoring_locations(id)` ON DELETE RESTRICT
  - `ingestion_run_id` $\rightarrow$ `ingestion_runs(id)` ON DELETE RESTRICT
- **Unique Constraint**: `uq_pm25_observations_location_observed_at (location_id, observed_at)`
- **Check Constraints**:
  - `ck_pm25_observations_non_negative_value`: `value_ug_m3 >= 0`
  - `ck_pm25_observations_unit`: `unit = 'ug/m3'`
- **Description**: Ground-truth hourly PM2.5 observations from OpenAQ.

### 3. `weather_records`
- **Primary Key**: `id (UUID)`
- **Foreign Keys**:
  - `location_id` $\rightarrow$ `monitoring_locations(id)` ON DELETE RESTRICT
  - `ingestion_run_id` $\rightarrow$ `ingestion_runs(id)` ON DELETE RESTRICT
- **Unique Constraint**: `uq_weather_records_location_valid_at (location_id, valid_at)`
- **Check Constraints**:
  - `ck_weather_records_humidity_range`: `0 <= humidity_percent <= 100`
  - `ck_weather_records_non_negative_wind_speed`: `wind_speed_kmh >= 0`
  - `ck_weather_records_positive_surface_pressure`: `surface_pressure_hpa > 0`
  - `ck_weather_records_wind_direction_range`: `0 <= wind_direction_degrees <= 360`
  - `ck_weather_records_non_negative_precipitation`: `precipitation_mm >= 0`
  - `ck_weather_records_non_negative_radiation`: `shortwave_radiation_w_m2 >= 0`
- **Description**: Hourly weather observations and forecasts from Open-Meteo.

### 4. `forecast_runs`
- **Primary Key**: `id (UUID)`
- **Check Constraint**: `status IN ('running', 'succeeded', 'failed')`
- **Description**: Tracks operational model execution cycles, input snapshot hashes, and failure diagnostics.

### 5. `forecasts`
- **Primary Key**: `id (UUID)`
- **Foreign Key**: `forecast_run_id` $\rightarrow$ `forecast_runs(id)` ON DELETE RESTRICT
- **Unique Constraint**: `uq_forecasts_run_horizon (forecast_run_id, horizon_hours)`
- **Check Constraints**:
  - `ck_forecasts_supported_horizon`: `horizon_hours IN (1, 6, 24)`
  - `ck_forecasts_non_negative_prediction`: `predicted_value_ug_m3 >= 0`
  - `ck_forecasts_non_negative_lower_bound`: `lower_bound_ug_m3 >= 0`
  - `ck_forecasts_ordered_bounds`: `upper_bound_ug_m3 >= lower_bound_ug_m3`
- **Description**: Multi-horizon predictions with conformal prediction bounds.

### 6. `forecast_explanations`
- **Primary Key**: `id (UUID)`
- **Foreign Key**: `forecast_id` $\rightarrow$ `forecasts(id)` ON DELETE CASCADE
- **Unique Constraint**: `uq_forecast_explanations_forecast (forecast_id)` (1-to-1 with `forecasts`)
- **Description**: Stores explainable AI (XAI) feature importance rankings and contributions for each prediction.

### 7. `alert_preferences`
- **Primary Key**: `id (UUID)`
- **Unique Constraint**: `uq_alert_preferences_browser_id (browser_id)`
- **Check Constraint**: `threshold_ug_m3 > 0 AND threshold_ug_m3 <= 2000`
- **Description**: Anonymous browser client alert thresholds.

### 8. `ingestion_runs`
- **Primary Key**: `id (UUID)`
- **Check Constraints**:
  - `ck_ingestion_runs_source_type`: `source_type IN ('pm25', 'weather')`
  - `ck_ingestion_runs_status`: `status IN ('running', 'succeeded', 'failed')`
- **Description**: Audit trail for each automated ingestion attempt.

### 9. `system_events`
- **Primary Key**: `id (UUID)`
- **Check Constraint**: `level IN ('info', 'warning', 'error')`
- **Description**: Operational logging and reliability telemetry table.
