#!/bin/bash
set -euo pipefail

cd "$FLY_WORKING_DIR"

if flyctl status --app "$FLY_APP_NAME" >/dev/null 2>&1; then
  echo "App $FLY_APP_NAME exists — skipping launch."
else
  echo "App $FLY_APP_NAME does not exist — launching..."
  flyctl launch --no-deploy --yes --name "$FLY_APP_NAME" --region "$FLY_REGION"
fi

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  flyctl secrets set "$line" --app "$FLY_APP_NAME"
done <<<"$FLY_SECRETS"

echo "Deploying $FLY_APP_NAME..."
flyctl deploy --yes --app "$FLY_APP_NAME" --strategy immediate
