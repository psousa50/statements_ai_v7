#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"

cd "$ROOT_DIR/bank-statements-api"
pip install uv
uv sync
