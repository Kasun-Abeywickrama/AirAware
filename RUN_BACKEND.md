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

## Recommended development mode: backend locally, PostgreSQL in Docker

You do not need to build the frontend and backend Docker images for every code change. Run only PostgreSQL in Docker, and run FastAPI directly on your computer. This downloads the PostgreSQL image once, but avoids rebuilding the Python and frontend images.

### First-time local setup

Create a virtual environment and install the backend dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

Make sure `.env` contains this local database URL:

```text
DATABASE_URL=postgresql+psycopg://airaware:airaware_dev_password@localhost:5432/airaware
```

Start only the PostgreSQL container from the project root:

```powershell
docker compose up -d postgres
```

Apply the database migrations from the `backend` folder:

```powershell
Set-Location backend
python -m alembic upgrade head
```

### Start FastAPI locally

Keep this terminal open:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The local API is now available at:

- API docs: `http://localhost:8000/docs`
- System status: `http://localhost:8000/api/v1/status`
- Latest forecasts: `http://localhost:8000/api/v1/forecasts/latest`

The local backend reads the trained files from `backend/model_artifacts`. If they are not present, copy them once using the command in the first-time section above.

### Generate data and forecasts manually

Open a second PowerShell terminal. From the `backend` folder, run:

```powershell
Set-Location backend
python -m app.setup_station
python -m app.workers.ingest
python -m app.workers.forecast
```

The last command creates new forecasts and their explanations. Existing forecasts created before migration `0009_add_forecast_explanations` will not contain explanations, so generate a fresh forecast after migrating.

For an automatic hourly development worker, use a third terminal:

```powershell
Set-Location backend
python -m app.workers.scheduler
```

Stop the local API with `Ctrl+C`. Stop only PostgreSQL when you finish:

```powershell
docker compose stop postgres
```

### Run the frontend against the local backend

Open another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite forwards `/api` requests to the locally running API at `http://localhost:8000`.

## Full Docker mode

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
