#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
source "$ROOT_DIR/bin/env.sh"

cd "$ROOT_DIR/bank-statements-api"
DATABASE_URL="$TEST_DATABASE_URL" uv run alembic upgrade head
