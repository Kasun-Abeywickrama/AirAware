@echo off
setlocal
title AirAware Local Stopper
cd /d "%~dp0"

echo ==================================================
echo    Stopping all AirAware local services...
echo ==================================================

echo Freeing ports 8000 and 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do (
    echo   Stopping process %%a on port 8000...
    taskkill /f /pid %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173.*LISTENING"') do (
    echo   Stopping process %%a on port 5173...
    taskkill /f /pid %%a 2>nul
)

echo Stopping lingering background workers...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*app.workers.scheduler*' -or $_.CommandLine -like '*app.main:app*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" 2>nul

echo Stopping PostgreSQL container...
docker compose stop postgres

echo.
echo ==================================================
echo    All AirAware local services have been stopped.
echo ==================================================
echo.
timeout /t 3
