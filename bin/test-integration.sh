#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
source "$ROOT_DIR/bin/env.sh"

cleanup() {
    echo "Cleaning up..."
    cd "$ROOT_DIR" && pnpm run test:db:down 2>/dev/null || true
}

trap cleanup EXIT

cd "$ROOT_DIR"
pnpm run test:db:up
pnpm run test:db:migrate

cd "$ROOT_DIR/bank-statements-api"
DATABASE_URL="$TEST_DATABASE_URL" uv run pytest tests/integration -v "$@"
