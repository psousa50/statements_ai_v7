#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
source "$ROOT_DIR/bin/env.sh"

cd "$ROOT_DIR/bank-statements-api"
uv run isort . --check-only
uv run black . --check
uv run ruff check .
