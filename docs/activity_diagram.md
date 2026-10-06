# AirAware – Activity Diagrams

## 1. Overview
The Activity Diagrams illustrate the step-by-step business logic, decision gates, guardrails, and exception-handling pathways in AirAware.

Two key workflows are modeled:
1. **Live Data Ingestion & Staleness Guardrail Decision Flow**
2. **Operational Machine Learning Forecast Generation Pipeline**

---

## 2. Activity Diagram 1: Live Ingestion & Staleness Guardrails

```mermaid
flowchart TD
    Start([Start Ingestion Cycle]) --> InitRun[Initialize IngestionRun in DB]
    InitRun --> QueryOpenAQ[Query OpenAQ REST API for Station]
    
    QueryOpenAQ --> CheckOpenAQResp{HTTP 200 & Valid Payload?}
    CheckOpenAQResp -- No --> LogOpenAQFail[Mark PM2.5 Ingestion as Failed<br/>Log ProviderError Event]
    LogOpenAQFail --> NextWeather
    
    CheckOpenAQResp -- Yes --> CheckAge{Observation Age ≤ 180 min?}
    CheckAge -- No (Stale Sensor) --> StaleReject[Reject Reading: ObservationTooOldError<br/>Mark IngestionRun 'failed']
    StaleReject --> SetLimited[Update System Status to 'Limited Service']
    SetLimited --> NextWeather
    
    CheckAge -- Yes (Fresh Data) --> ValidatePM[Validate PM2.5 Value & Canonical Unit ug/m³]
    ValidatePM --> SavePM[Upsert Pm25Observation into DB]
    SavePM --> MarkPMSucceed[Mark PM2.5 IngestionRun 'succeeded']
    
    MarkPMSucceed --> NextWeather[Query Open-Meteo for Hourly Weather]
    NextWeather --> CheckMeteoResp{HTTP 200 & Complete Metrics?}
    CheckMeteoResp -- No --> LogMeteoFail[Mark Weather Ingestion as Failed<br/>Log ProviderError Event]
    LogMeteoFail --> IngestEnd
    
    CheckMeteoResp -- Yes --> ValidateMeteo[Validate Temperature, Humidity, Wind & Radiation]
    ValidateMeteo --> SaveWeather[Bulk Insert WeatherRecord into DB]
    SaveWeather --> MarkWeatherSucceed[Mark Weather IngestionRun 'succeeded']
    
    MarkWeatherSucceed --> IngestEnd([End Ingestion Cycle])
    SetLimited --> IngestEnd
```

---

## 3. Activity Diagram 2: Operational ML Forecast Generation Pipeline

```mermaid
flowchart TD
    StartForecast([Start Forecast Pipeline]) --> CheckLags[Query DB for Past 168 Hours of PM2.5 Lags]
    CheckLags --> VerifyHistory{Complete 168 Lags Available?}
    
    VerifyHistory -- No --> LogMissingHistory[Log System Warning: 'PM2.5 history incomplete'<br/>Skip Model Execution]
    LogMissingHistory --> EndForecast([End Forecast Pipeline])
    
    VerifyHistory -- Yes --> CheckWeather{Target Horizon Weather Available?}
    CheckWeather -- No --> LogMissingWeather[Log Warning: 'Forecast weather incomplete'<br/>Skip Model Execution]
    LogMissingWeather --> EndForecast
    
    CheckWeather -- Yes --> LoadArtifacts[Verify SHA-256 Checksums & Load Pretrained Models]
    LoadArtifacts --> CheckChecksum{Checksums Match Manifest?}
    CheckChecksum -- No --> SecurityFail[Raise IntegrityError: Incompatible Artifacts]
    SecurityFail --> EndForecast
    
    CheckChecksum -- Yes --> BuildFeatures[Engineer Features:<br/>1. 168h PM2.5 Lags<br/>2. Weather Features<br/>3. Cyclic Hour & Day-of-Year Sin/Cos]
    
    BuildFeatures --> RunInference[Execute Model Inference for Horzions +6h, +12h, +24h]
    RunInference --> ComputeBounds[Calculate Conformal Prediction Intervals<br/>Lower & Upper Bounds]
    ComputeBounds --> CalcExplanations[Extract Top-3 Driving Features & Explanations]
    
    CalcExplanations --> DBTransaction[Begin Database Transaction]
    DBTransaction --> SaveRun[Insert ForecastRun Record]
    SaveRun --> BulkSaveForecasts[Bulk Insert Forecasts & Explanations]
    BulkSaveForecasts --> CommitDB[Commit Transaction & Log SystemEvent 'info']
    CommitDB --> EndForecast
```
