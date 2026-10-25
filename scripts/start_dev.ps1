# MediVault Enterprise Development Startup Script (PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Starting MediVault AI Enterprise Hospital Operating System" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Run migrations / seeding
Write-Host "[1/3] Running database seeder..." -ForegroundColor Yellow
python scripts/seed_db.py

# 2. Start HOS Backend
Write-Host "[2/3] Launching Backend HOS API on port 8088..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn main_enterprise:app --host 127.0.0.1 --port 8088 --reload"

# 3. Start Frontend
Write-Host "[3/3] Launching Vite Frontend on port 5173..." -ForegroundColor Yellow
Set-Location -Path "medivault-ai/frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev -- --host 127.0.0.1 --port 5173"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "All systems operational!" -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:5173/" -ForegroundColor White
Write-Host "Backend API: http://127.0.0.1:8088/" -ForegroundColor White
Write-Host "API Docs: http://127.0.0.1:8088/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
