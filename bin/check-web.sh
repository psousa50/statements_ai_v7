#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"

cd "$ROOT_DIR/bank-statements-web"
pnpm exec tsc --noEmit
pnpm run lint
pnpm run format:check
