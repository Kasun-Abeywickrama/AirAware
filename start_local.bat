@echo off
title AirAware Local Launcher
cd /d "%~dp0"

echo ==================================================
echo    AirAware - Starting Application Locally        
echo ==================================================

echo.
echo [1/5] Stopping any currently running instances...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173.*LISTENING"') do taskkill /f /pid %%a 2>nul
powershell -NoProfile -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*app.workers.scheduler*' -or $_.CommandLine -like '*app.main:app*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" 2>nul

rem Stop any conflicting non-AirAware containers occupying port 5432
powershell -NoProfile -Command "docker ps --format '{{.ID}} {{.Names}} {{.Ports}}' | Where-Object { $_ -like '*5432*' -and $_ -notlike '*airaware-postgres*' } | ForEach-Object { ($_ -split ' ')[0] } | ForEach-Object { docker stop $_ }" >nul 2>nul

echo [2/5] Verifying environment and model artifacts...
if not exist ".env" (
    copy .env.example .env >nul
    echo   Created .env from .env.example
)
if not exist "backend\model_artifacts" mkdir "backend\model_artifacts"
if not exist "backend\model_artifacts\1h_gru.pt" (
    if exist "..\Main Research\03_Forecasting\outputs\operational\artifacts\1h_gru.pt" (
        copy "..\Main Research\03_Forecasting\outputs\operational\artifacts\*" "backend\model_artifacts\" >nul
        echo   Copied model artifacts to backend\model_artifacts
    )
)

echo [3/5] Starting PostgreSQL database...
docker compose up -d postgres
echo   Waiting for PostgreSQL to accept connections...
for /l %%i in (1,1,20) do (
    docker compose exec -T postgres pg_isready -U airaware -d airaware >nul 2>nul
    if not errorlevel 1 goto pg_ready
    timeout /t 1 /nobreak >nul
)
:pg_ready
echo   PostgreSQL is ready.

echo [4/5] Initializing database schema and station...
if not exist ".venv" (
    echo   Creating Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install -r backend\requirements.txt
)

call .venv\Scripts\activate.bat
cd backend
python -m alembic upgrade head
python -m app.setup_station
cd ..

if not exist "frontend\node_modules" (
    echo   Installing frontend packages...
    cd frontend
    call npm install
    cd ..
)

echo [5/5] Launching Backend, Worker, and Frontend...
start "AirAware Backend" cmd /k "cd /d "%~dp0backend" && call "%~dp0.venv\Scripts\activate.bat" && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "AirAware Worker" cmd /k "cd /d "%~dp0backend" && call "%~dp0.venv\Scripts\activate.bat" && python -m app.workers.scheduler"
start "AirAware Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

ping 127.0.0.1 -n 4 >nul
start http://localhost:5173

echo.
echo ==================================================
echo    AirAware is running successfully!
echo    Dashboard:  http://localhost:5173
echo    API Docs:   http://localhost:8000/docs
echo ==================================================
echo To stop all services anytime, double-click: stop_local.bat
echo.
pause
