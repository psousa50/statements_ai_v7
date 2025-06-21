#!/bin/bash

# Get API URL from environment or use default
API_URL="${API_BASE_URL:-http://localhost:8000}/api/v1/statements/analyze"

echo "Analyzing transactions using API at: $API_URL"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/statements/100_BT_Records.csv",
    "account_id": "1"
  }'
