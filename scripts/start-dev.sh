#!/bin/bash

API_PORT=${API_PORT:-8010}
WEB_PORT=${WEB_PORT:-5173}

cleanup() {
    echo "Stopping services..."
    kill $backend_pid $frontend_pid 2>/dev/null
    exit 0
}

trap cleanup SIGINT

echo "Starting backend server..."
cd bank-statements-api
uv run python run.py &
backend_pid=$!

echo "Starting frontend server..."
cd ../bank-statements-web
pnpm run dev &
frontend_pid=$!

echo "Both services started. Press Ctrl+C to stop."
echo "Backend running on port $API_PORT"
echo "Frontend running on port $WEB_PORT"

wait $backend_pid $frontend_pid