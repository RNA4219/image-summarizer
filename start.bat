@echo off
REM Quick start script for Windows

echo === Image Summarizer Quick Start ===

REM Check .env exists
if not exist .env (
    echo Copying .env.example to .env...
    copy .env.example .env
    echo Please edit .env and set OPENAI_API_KEY
    pause
    exit /b 1
)

REM Start backend
echo Starting backend...
start "Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak > nul

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