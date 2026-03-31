@echo off
REM G.O.E. Terminal Startup Script (Windows)
REM This script starts both backend and frontend in separate terminals

echo ============================================
echo  G.O.E. TERMINAL ^| Global Ontology Engine
echo  Development Startup Script
echo ============================================
echo.

REM Check if venv is activated
python -c "import sys; print(sys.prefix)" | find "venv" >nul
if errorlevel 1 (
    echo Activating Python virtual environment...
    call venv\Scripts\Activate.ps1
)

REM Start backend in a new window
echo Starting backend server...
start "Backend - FastAPI" powershell -NoExit -Command "cd . ; .\venv\Scripts\Activate.ps1 ; uvicorn backend.main:app --reload --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak

REM Start frontend in a new window
echo Starting frontend development server...
start "Frontend - Vite" powershell -NoExit -Command "cd frontend ; npm run dev"

echo.
echo ============================================
echo  Servers starting...
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo ============================================
echo.
