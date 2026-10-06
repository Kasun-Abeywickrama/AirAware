# Run AirAware with Docker

### 1. Setup Environment & Model Artifacts
```powershell
# 1. Create .env file and add your OPENAQ_API_KEY inside it
Copy-Item .env.example .env

# 2. Copy the trained model artifacts
New-Item -ItemType Directory -Force backend/model_artifacts
Copy-Item "..\Main Research\03_Forecasting\outputs\operational\artifacts\*" backend\model_artifacts\
```

---

### 2. Build & Start All Services
```powershell
docker compose up --build -d
```

---

### 3. Initialize Database & Seed Initial Data (First Time Only)
```powershell
# Apply database migrations
docker compose exec backend python -m alembic upgrade head

# Register monitoring station
docker compose exec backend python -m app.setup_station

# Fetch live data and generate initial forecasts
docker compose exec backend python -m app.workers.ingest
docker compose exec backend python -m app.workers.forecast
```

---

### 4. Access URLs
- **Web Dashboard:** `http://localhost:5173`
- **API Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`
- **System Status:** `http://localhost:8000/api/v1/status`

---

### 5. Management Commands
```powershell
# Check running containers
docker compose ps

# View logs
docker compose logs -f
docker compose logs -f worker

# Manual live data update on demand
docker compose exec backend python -m app.workers.ingest
docker compose exec backend python -m app.workers.forecast

# Run backend tests inside Docker
docker compose exec backend python -m pytest tests

# Stop containers (preserves database data)
docker compose down

# Stop & wipe database volume (clean reset)
docker compose down -v
```
