#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"

cd "$ROOT_DIR/bank-statements-api"
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
