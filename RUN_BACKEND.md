# Run AirAware Backend

Run these commands from the project root (`FYP-Project`) in PowerShell.

## First time only

1. Create your private environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Open `.env` and add your private `OPENAQ_API_KEY`.

3. Copy the trained model files:

   ```powershell
   New-Item -ItemType Directory -Force backend/model_artifacts
   Copy-Item ..\..\..\Forecasting\outputs\operational\artifacts\1h_gru.pt, ..\..\..\Forecasting\outputs\operational\artifacts\1h_tree.joblib, ..\..\..\Forecasting\outputs\operational\artifacts\6h_gru.pt, ..\..\..\Forecasting\outputs\operational\artifacts\6h_tree.joblib, ..\..\..\Forecasting\outputs\operational\artifacts\24h_tree.joblib backend/model_artifacts
   ```

Do not commit `.env` or `backend/model_artifacts`.

## Start the backend

```powershell
docker compose up --build
```

The first build can take longer because Docker downloads Python packages. Later starts are faster.

Open these links:

- API docs: `http://localhost:8000/docs`
- System status: `http://localhost:8000/api/v1/status`
- Current PM2.5: `http://localhost:8000/api/v1/current-conditions`
- Latest forecasts: `http://localhost:8000/api/v1/forecasts/latest`

The worker starts automatically and collects data every hour.

## Run one update now

Use this when you want fresh data and forecasts immediately:

```powershell
docker compose exec backend python -m app.setup_station
docker compose exec backend python -m app.workers.ingest
docker compose exec backend python -m app.workers.forecast
```

## Stop the backend

```powershell
docker compose down
```

Your PostgreSQL development data remains saved. Use `docker compose up` later to start it again.
