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

This command shows the current migration revision. Apply all migrations in Docker with:

```powershell
docker compose exec backend python -m alembic upgrade head
```

## Manual live ingestion

Add your private OpenAQ API key to `.env`, then run the following from the repository root:

```powershell
docker compose exec backend python -m app.setup_station
docker compose exec backend python -m app.workers.ingest
```

The command collects the latest PM2.5 value plus seven days of hourly PM2.5 history from OpenAQ. It also collects the full weather inputs required by the packaged operational models from Open-Meteo. It records separate PM2.5 and weather outcomes and exits with an error if either source fails.

The backend does not generate forecasts yet. The next milestone adds the existing trained AirAware model artifacts after live input readiness is confirmed.

## Run tests

From the repository root:

```powershell
python -m pytest backend/tests
```
