#!/bin/bash
set -euo pipefail

cd "$FLY_WORKING_DIR"

if [ ! -f fly.toml ]; then
  echo "fly.toml not found — launching app $FLY_APP_NAME..."
  flyctl launch --no-deploy --name "$FLY_APP_NAME" --region "$FLY_REGION"
else
  echo "fly.toml exists — skipping launch."
fi

echo "Setting secrets for app $FLY_APP_NAME..."
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  flyctl secrets set "$line" --app "$FLY_APP_NAME"
done <<<"$FLY_SECRETS"

echo "Deploying $FLY_APP_NAME..."
flyctl deploy --app "$FLY_APP_NAME" --strategy immediate
