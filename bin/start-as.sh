#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
EMAIL="${1:-$(git config user.email)}"

if [ -z "$EMAIL" ]; then
  echo "Usage: pnpm start:as [email]   (defaults to git config user.email)" >&2
  exit 1
fi

echo "Starting in E2E mode as: $EMAIL"
export E2E_TEST_MODE=true
export E2E_TEST_LOGIN_EMAIL="$EMAIL"
cd "$ROOT_DIR"
exec pnpm run start
