#!/bin/bash
set -e

echo "=========================================================="
echo "Starting MediVault AI Enterprise Hospital Operating System"
echo "=========================================================="

echo "[1/3] Running database seeder..."
python scripts/seed_db.py

echo "[2/3] Starting Backend HOS API on port 8088 in background..."
python -m uvicorn main_enterprise:app --host 127.0.0.1 --port 8088 --reload &
BACKEND_PID=$!

echo "[3/3] Starting Vite Frontend on port 5173..."
cd medivault-ai/frontend
npm run dev -- --host 127.0.0.1 --port 5173
