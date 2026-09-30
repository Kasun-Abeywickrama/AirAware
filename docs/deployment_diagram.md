# AirAware – Deployment Diagram

## 1. Overview
The Deployment Diagram illustrates the physical and containerized architecture of **AirAware**, including network protocols, port mappings, inter-container communication, persistent storage volumes, and external API integrations.

---

## 2. Mermaid Deployment Diagram

```mermaid
graph TB
    subgraph ClientDevice["Client Tier (User Machine)"]
        Browser["Web Browser (Chrome / Edge / Firefox / Safari)<br/>React SPA Client"]
    end

    subgraph DockerHost["Docker Host / Application Server"]
        subgraph FrontendContainer["Frontend Container (Nginx Alpine)"]
            Nginx["Nginx Web Server<br/>Port: 80 (Host mapped to 5173)<br/>Serves HTML, JS, CSS, Assets"]
        end

        subgraph BackendContainer["Backend Container (Python 3.12)"]
            FastAPI["Uvicorn ASGI Server<br/>FastAPI Web Application<br/>Port: 8000<br/>Endpoints: /api/v1/*"]
        end

        subgraph WorkerContainer["Worker Container (Python 3.12)"]
            Scheduler["Background Scheduler Daemon<br/>Command: python -m app.workers.scheduler<br/>Cadence: Hourly (3600s)"]
            Workers["Ingestion & Forecasting Workers"]
        end

        subgraph DatabaseContainer["Database Container (PostgreSQL 17 Alpine)"]
            Postgres["PostgreSQL Database Engine<br/>Port: 5432<br/>Database: airaware"]
        end

        subgraph StorageVolumes["Storage Volumes"]
            ModelVol[("Local Model Artifacts Directory<br/>./backend/model_artifacts<br/>(Mounted Read-Only :ro)")]
            DBVol[("Docker Named Volume<br/>postgres_data<br/>(/var/lib/postgresql/data)")]
        end
    end

    subgraph ExternalServices["External Cloud Providers"]
        OpenAQ["OpenAQ REST API v3<br/>https://api.openaq.org<br/>(Port 443 HTTPS)"]
        OpenMeteo["Open-Meteo Weather API<br/>https://api.open-meteo.com<br/>(Port 443 HTTPS)"]
    end

    %% Network Connections
    Browser -- "HTTP / HTTPS (Port 5173)" --> Nginx
    Browser -- "REST JSON Requests (Port 8000)" --> FastAPI

    FastAPI -- "SQLAlchemy / psycopg (Port 5432)" --> Postgres
    WorkerContainer -- "SQLAlchemy / psycopg (Port 5432)" --> Postgres

    WorkerContainer -- "HTTPS (Port 443) with X-API-Key" --> OpenAQ
    WorkerContainer -- "HTTPS (Port 443)" --> OpenMeteo
    FastAPI -.-> OpenAQ

    %% Volume Mounts
    ModelVol -.->|"Mount :ro"| BackendContainer
    ModelVol -.->|"Mount :ro"| WorkerContainer
    DBVol --- DatabaseContainer
```

---

## 3. Node Specifications & Port Configuration

| Node / Container | Base Image / Technology | Network Ports | Purpose |
| :--- | :--- | :--- | :--- |
| **`ClientDevice`** | Web Browser | N/A | Renders client UI, charts, and activity planner interactive clock. |
| **`frontend`** | `node:20-alpine` (builder) / `nginx:alpine` | `5173:80` | Serves compiled static Vite production bundle. |
| **`backend`** | `python:3.12-slim` | `8000:8000` | Exposes REST APIs for status, observations, forecasts, and planner. |
| **`worker`** | `python:3.12-slim` | Internal | Runs background hourly cycle (`ingest` $\rightarrow$ `forecast`). |
| **`postgres`** | `postgres:17-alpine` | `5432:5432` | Relational persistence with healthcheck (`pg_isready`). |
| **`postgres_data`** | Docker Named Volume | Local Disk | Persists PM2.5 readings, forecasts, and logs across restarts. |
| **`model_artifacts`** | Host Directory Mount | Local Disk | Houses pre-trained ML models (`.pkl`, `.pt`) verified via SHA-256. |
