#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"

cd "$ROOT_DIR/bank-statements-web"
pnpm install --frozen-lockfile
pnpm run build
