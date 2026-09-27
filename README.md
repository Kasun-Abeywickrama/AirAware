# AirAware

AirAware is a New Delhi PM2.5 decision-support web application. This repository currently contains the backend foundation only.

## Start with Docker

1. Copy `.env.example` to `.env`.
2. Run:

   ```powershell
   docker compose up --build
   ```

3. Open:
   - Health check: `http://localhost:8000/health`
   - API documentation: `http://localhost:8000/docs`

Stop the containers with `docker compose down`.

The database readiness check is available at `http://localhost:8000/health/database`.

## Run the backend locally

Install dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Start the API:

```powershell
python -m uvicorn backend.app.main:app --reload
```

Copy `.env.example` to `.env` first. The local `DATABASE_URL` in that file uses `localhost`; Docker Compose automatically uses the `postgres` service instead.

## Check migrations

From the `backend` folder, run:

```powershell
python -m alembic current
```

There are no application tables or migration revisions in this foundation segment.

## Manual live ingestion

Add your private OpenAQ API key to `.env`, then run the following from the repository root:

```powershell
docker compose exec backend python -m app.setup_station
docker compose exec backend python -m app.workers.ingest
```

The command collects PM2.5 from OpenAQ and hourly weather from Open-Meteo. It records separate PM2.5 and weather outcomes and exits with an error if either source fails.

## Run tests

From the repository root:

```powershell
python -m pytest backend/tests
```
