#!/bin/bash
# Quick start script for macOS/Linux

echo "=== Image Summarizer Quick Start ==="

# Check .env exists
if [ ! -f .env ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "Please edit .env and set OPENAI_API_KEY"
    exit 1
fi

# Start backend
echo "Starting backend..."
cd backend
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -q
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend..."
cd frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop servers"

# Wait for Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" SIGINT
wait