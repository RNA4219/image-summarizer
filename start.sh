#!/bin/bash
# Quick start script for macOS/Linux
# Run from project root directory

set -e  # Exit on error

echo "=== Image Summarizer Quick Start ==="

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check .env exists
if [ ! -f .env ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env and set OPENAI_API_KEY before running again."
    echo ""
    exit 1
fi

# Check backend venv exists
if [ ! -d backend/.venv ]; then
    echo "Creating backend virtual environment..."
    cd backend
    python3 -m venv .venv
    cd "$SCRIPT_DIR"
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd "$SCRIPT_DIR"

# Check frontend node_modules exists
if [ ! -d frontend/node_modules ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd "$SCRIPT_DIR"
fi

echo ""
echo "Starting servers..."
echo ""

# Start backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
deactivate
cd "$SCRIPT_DIR"

# Wait for backend
sleep 3

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop servers"
echo ""

# Handle Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait