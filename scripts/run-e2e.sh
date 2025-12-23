#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
API_PORT=${API_PORT:-8010}

cleanup() {
    echo "Cleaning up..."
    pkill -f 'uv run python run.py' 2>/dev/null || true
    cd "$ROOT_DIR" && pnpm run test:db:down 2>/dev/null || true
}

trap cleanup EXIT

cd "$ROOT_DIR/e2e/bank-statements-web"
pnpm exec playwright install chromium

cd "$ROOT_DIR"
pnpm run test:db:up
sleep 2
pnpm run test:db:migrate

cd "$ROOT_DIR/bank-statements-api"
E2E_TEST_MODE=true API_PORT=$API_PORT DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:15432/bank_statements_test uv run python run.py &
sleep 3

cd "$ROOT_DIR/e2e/bank-statements-web"
if [[ "$1" == "--ui" ]]; then
    API_BASE_URL=http://localhost:$API_PORT VITE_API_URL=http://localhost:$API_PORT pnpm run test:ui --project=chromium
else
    API_BASE_URL=http://localhost:$API_PORT VITE_API_URL=http://localhost:$API_PORT pnpm run test --project=chromium "$@"
fi
