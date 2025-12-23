#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
API_PORT=${API_PORT:-8000}

cleanup() {
    echo "Cleaning up..."
    cd "$ROOT_DIR" && docker-compose down 2>/dev/null || true
}

trap cleanup EXIT

cd "$ROOT_DIR"

echo "Starting services with docker-compose..."
E2E_TEST_MODE=true API_PORT=$API_PORT docker-compose up -d db api

echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:$API_PORT/health > /dev/null 2>&1; then
        echo "API is ready"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

if ! curl -s http://localhost:$API_PORT/health > /dev/null 2>&1; then
    echo "API failed to start"
    docker-compose logs api
    exit 1
fi

cd "$ROOT_DIR/e2e/bank-statements-web"
pnpm exec playwright install chromium

echo "Running E2E tests..."
if [[ "$1" == "--ui" ]]; then
    VITE_API_URL=http://localhost:$API_PORT pnpm run test:ui --project=chromium
else
    VITE_API_URL=http://localhost:$API_PORT pnpm run test --project=chromium "$@"
fi
