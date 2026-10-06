# AirAware – Sequence Diagrams

## 1. Overview
The Sequence Diagrams model the dynamic runtime interactions between frontend components, backend services, external APIs, and the PostgreSQL database.

Two critical flows are modeled:
1. **Automated Ingestion & Machine Learning Forecasting Pipeline** (System workflow)
2. **Activity Planning & Optimal Window Generation** (User interaction workflow)

---

## 2. Diagram 1: Automated Ingestion & Operational ML Forecasting

This sequence runs automatically every hour via the worker daemon (`python -m app.workers.scheduler`).

```mermaid
sequenceDiagram
    autonumber
    actor Scheduler as Background Scheduler
    participant Ingest as Ingestion Worker
    participant OpenAQ as OpenAQ API
    participant OpenMeteo as Open-Meteo API
    participant DB as PostgreSQL Database
    participant ForecastWorker as Forecast Worker
    participant ML as PackagedModelService
    participant Artifacts as Local Model Files (.pkl / .pt)

    Note over Scheduler, Ingest: Step 1: Automated Ingestion Phase
    Scheduler->>Ingest: Trigger hourly ingestion cycle
    Ingest->>DB: Start IngestionRun (source="pm25")
    Ingest->>OpenAQ: GET /locations/{id}/latest & /sensors/{id}/hours
    OpenAQ-->>Ingest: Return latest PM2.5 reading & lag hours
    
    alt Observation age > 180 minutes (Stale)
        Ingest->>DB: Mark IngestionRun "failed" (ObservationTooOldError)
        Ingest->>DB: Log SystemEvent (Severity: WARNING)
    else Observation is Fresh (≤ 180 min)
        Ingest->>DB: Insert Pm25Observation records
        Ingest->>DB: Mark IngestionRun "succeeded"
    end

    Ingest->>DB: Start IngestionRun (source="weather")
    Ingest->>OpenMeteo: GET /v1/forecast (lat, lon, hourly variables)
    OpenMeteo-->>Ingest: Return hourly weather metrics
    Ingest->>DB: Insert WeatherRecord rows
    Ingest->>DB: Mark IngestionRun "succeeded"

    Note over Scheduler, ForecastWorker: Step 2: Guarded Forecast Generation Phase
    Scheduler->>ForecastWorker: Trigger forecast generation
    ForecastWorker->>DB: Query last 168 hours of PM2.5 & weather
    
    alt History incomplete (< 168 hours)
        ForecastWorker->>DB: Record SystemEvent ("Forecast history incomplete")
    else Complete 168-Hour History Available
        ForecastWorker->>ML: generate_forecasts(pm25_lags, weather_records)
        ML->>Artifacts: Verify SHA-256 checksums & load weights
        Artifacts-->>ML: Pretrained GRU, XGBoost & Conformal bounds
        ML->>ML: Build feature vector (lags + weather + hour/doy sin/cos)
        ML->>ML: Run model inference (+6h, +12h, +24h, +48h)
        ML->>ML: Compute conformal confidence intervals & feature impacts
        ML-->>ForecastWorker: Return ForecastResult (points, bounds, explanations)
        ForecastWorker->>DB: Insert ForecastRun
        ForecastWorker->>DB: Bulk insert Forecast & ForecastExplanation rows
        ForecastWorker->>DB: Log SystemEvent ("Operational forecasts generated")
    end
```

---

## 3. Diagram 2: Activity Planner Request Workflow

This sequence models a user looking for the cleanest outdoor exercise or commuting window.

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Athlete
    participant UI as ActivityPlannerPage (React)
    participant API as FastAPI Router (/api/v1/activity-plan)
    participant Service as ActivityPlannerService
    participant DB as PostgreSQL Database

    User->>UI: Selects Date (e.g. 2026-10-01) & Duration (e.g. 2 hours)
    User->>UI: Clicks "Find best times"
    UI->>API: GET /api/v1/activity-plan?date=2026-10-01&duration_minutes=120
    API->>Service: plan_activity(date, duration_minutes)
    
    Service->>DB: Query latest ForecastRun & Forecast rows for target date
    DB-->>Service: Return hourly predicted values & upper bounds
    
    alt No forecasts available for requested date
        Service-->>API: Raise UnavailableError ("No complete plan available")
        API-->>UI: HTTP 503 / UnavailablePanel
        UI-->>User: Display "Try a different future date or duration"
    else Forecasts available
        Service->>Service: Slide duration window across day (00:00 to 23:59)
        Service->>Service: Compute mean PM2.5 & mean upper bound for each candidate
        Service->>Service: Rank windows by lowest exposure
        Service->>Service: Select top non-overlapping recommended windows
        Service-->>API: Return ActivityPlan (windows, metadata, disclaimer)
        API-->>UI: HTTP 200 JSON Response
        UI->>UI: Update state & pin default "Clock" visual mode
        UI-->>User: Render Clock Face timeline, Option Cards, and Data Table
    end
```
