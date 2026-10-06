# Run AirAware Locally

### 🚀 One-Click Start & Stop
- **Start:** Double-click `start_local.bat`  
  *Automatically stops any lingering services, starts PostgreSQL, runs database migrations, launches Backend, Worker, Frontend, and opens your browser.*
- **Stop:** Double-click `stop_local.bat`  
  *Stops Backend, Frontend, Worker, and the PostgreSQL container.*

---

### Manual Step-by-Step Setup

### 1. Setup Environment & Model Artifacts
```powershell
# 1. Create .env file and add your OPENAQ_API_KEY inside it
Copy-Item .env.example .env

# 2. Copy the trained model artifacts
New-Item -ItemType Directory -Force backend/model_artifacts
Copy-Item "..\Main Research\03_Forecasting\outputs\operational\artifacts\*" backend\model_artifacts\
```

---

### 2. Start PostgreSQL
```powershell
docker compose up -d postgres
```

---

### 3. Backend Setup & Run (Terminal 1)
```powershell
# Setup virtual environment and dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt

# Run migrations and configure station
Set-Location backend
python -m alembic upgrade head
python -m app.setup_station

# Fetch live data and generate initial forecasts
python -m app.workers.ingest
python -m app.workers.forecast

# Start FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Status: `http://localhost:8000/api/v1/status`

---

### 4. Background Scheduler (Optional - Terminal 2)
Runs automated hourly ingestion and forecasting:
```powershell
.\.venv\Scripts\Activate.ps1
Set-Location backend
python -m app.workers.scheduler
```

---

### 5. Frontend Run (Terminal 3)
```powershell
Set-Location frontend
npm install
npm run dev
```
- Dashboard: `http://localhost:5173`

---

### 6. Tests & Shutdown
```powershell
# Run backend tests
python -m pytest backend/tests

# Run frontend tests
Set-Location frontend; npm run test

# Stop PostgreSQL container
docker compose stop postgres
```
