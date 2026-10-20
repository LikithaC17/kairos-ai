#!/usr/bin/env bash
# Cross-platform startup script for Linux and macOS

set -e

echo "=================================================="
echo "  Starting NetForecast AI (Linux / macOS)"
echo "=================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/network-attack-forecasting"

# Check Python
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "Error: Python 3 is not installed or not in PATH."
    exit 1
fi

# Check Node & npm
if ! command -v npm &>/dev/null; then
    echo "Error: npm is not installed or not in PATH."
    exit 1
fi

# 1. Start FastAPI Backend
echo "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..."
cd "$PROJECT_DIR"
$PY_CMD -m uvicorn api.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# 2. Start Frontend
echo "[2/2] Starting React Dashboard on http://localhost:5173..."
cd "$PROJECT_DIR/dashboard"
if [ ! -d "node_modules" ]; then
    echo "Installing dashboard dependencies..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!

echo "=================================================="
echo "  NetForecast AI is now running!"
echo "  - Dashboard UI: http://localhost:5173"
echo "  - Backend API:  http://127.0.0.1:8000/docs"
echo "  Press CTRL+C to terminate both services."
echo "=================================================="

trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" INT TERM
wait
