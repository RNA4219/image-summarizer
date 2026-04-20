@echo off
REM Quick start script for Windows
REM Run from project root directory

echo === Image Summarizer Quick Start ===

REM Check .env exists
if not exist .env (
    echo Copying .env.example to .env...
    copy .env.example .env
    echo Please edit .env and set OPENAI_API_KEY
    pause
    exit /b 1
)

REM Setup backend
echo Setting up backend...
cd backend
if not exist .venv (
    py -3 -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt -q
cd ..

REM Start backend
echo Starting backend...
start "Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak > nul

REM Setup frontend
echo Setting up frontend...
cd frontend
call npm install --silent
cd ..

REM Start frontend
echo Starting frontend...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit (servers will keep running)
pause > nul