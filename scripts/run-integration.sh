#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cleanup() {
    echo "Cleaning up..."
    cd "$ROOT_DIR" && pnpm run test:db:down 2>/dev/null || true
}

trap cleanup EXIT

cd "$ROOT_DIR"
pnpm run test:db:up
sleep 3
pnpm run test:db:migrate

cd "$ROOT_DIR/bank-statements-api"
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:15432/bank_statements_test \
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:15432/bank_statements_test \
uv run pytest tests/integration -v "$@"
