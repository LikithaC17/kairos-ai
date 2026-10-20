@echo off
REM Cross-platform startup script for Windows

echo ==================================================
echo   Starting NetForecast AI (Windows)
echo ==================================================

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%network-attack-forecasting

REM 1. Start FastAPI Backend in new window
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "NetForecast AI - Backend (FastAPI)" cmd /k "cd /d "%PROJECT_DIR%" && python -m uvicorn api.app:app --host 127.0.0.1 --port 8000"

REM 2. Start React Dashboard in new window
echo [2/2] Starting React Dashboard on http://localhost:5173...
start "NetForecast AI - Frontend (Vite)" cmd /k "cd /d "%PROJECT_DIR%\dashboard" && npm run dev"

echo ==================================================
echo   NetForecast AI is now running!
echo   - Dashboard UI: http://localhost:5173
echo   - Backend API:  http://127.0.0.1:8000/docs
echo ==================================================
pause
