#!/bin/bash
set -euo pipefail

# Start backend in the background
echo "Starting backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Start frontend development server
echo "Starting frontend..."
cd frontend
npm run dev &

# Wait for both processes to finish
wait