@echo off
REM Quick start script for Windows
REM Run from project root directory

echo === Image Summarizer Quick Start ===

REM Check .env exists
if not exist .env (
    echo Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and set OPENAI_API_KEY before running again.
    echo.
    pause
    exit /b 1
)

REM Check backend venv exists
if not exist backend\.venv (
    echo Creating backend virtual environment...
    cd backend
    py -3 -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    cd ..
)

REM Install backend dependencies
echo Installing backend dependencies...
cd backend
call .venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)
cd ..

REM Check frontend node_modules exists
if not exist frontend\node_modules (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
    cd ..
)

echo.
echo Starting servers...
echo.

REM Start backend
start "Backend - Image Summarizer" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

REM Wait for backend
timeout /t 3 /nobreak > nul

REM Start frontend
start "Frontend - Image Summarizer" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause