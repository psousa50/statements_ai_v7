#!/bin/bash
set -euo pipefail

: "${GITHUB_OUTPUT:?Must be run within GitHub Actions with GITHUB_OUTPUT set}"

BRANCH_NAME="e2e-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"

RESPONSE=$(curl -s -X POST "https://console.neon.tech/api/v2/projects/${NEON_PROJECT_ID}/branches" \
  -H "Authorization: Bearer ${NEON_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "branch": {
      "name": "'"$BRANCH_NAME"'",
      "parent_id": "'"$NEON_TEMPLATE_BRANCH_ID"'"
    }
  }')

BRANCH_ID=$(jq -r '.branch.id' <<<"$RESPONSE")
DB_URL=$(jq -r '.branch.endpoints[0].connection_uri' <<<"$RESPONSE")

echo "branch_id=$BRANCH_ID" >>"$GITHUB_OUTPUT"
echo "db_url=$DB_URL" >>"$GITHUB_OUTPUT"
