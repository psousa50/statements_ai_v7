#!/bin/bash

# Function to cleanup background processes on exit
cleanup() {
    echo "Stopping services..."
    kill $backend_pid $frontend_pid 2>/dev/null
    exit 0
}

# Set up trap to catch Ctrl+C
trap cleanup SIGINT

echo "Starting backend server..."
cd bank-statements-api
poetry run python run.py &
backend_pid=$!

echo "Starting frontend server..."
cd ../bank-statements-web
pnpm run dev &
frontend_pid=$!

echo "Both services started. Press Ctrl+C to stop."
echo "Backend running on port 8010"
echo "Frontend running on port 6173"

# Wait for both processes
wait $backend_pid $frontend_pid