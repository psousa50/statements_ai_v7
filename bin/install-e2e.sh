#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"

cd "$ROOT_DIR/e2e/bank-statements-web"
pnpm install
