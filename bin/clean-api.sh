#!/bin/bash
ROOT_DIR="$(git rev-parse --show-toplevel)"

cd "$ROOT_DIR/bank-statements-api"
rm -rf __pycache__ .pytest_cache .coverage
