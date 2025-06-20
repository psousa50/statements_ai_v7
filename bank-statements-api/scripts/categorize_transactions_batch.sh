#!/bin/bash

# Get API URL from environment or use default
API_URL="${API_BASE_URL:-http://localhost:8000}/api/v1/transactions/categorize-batch"

echo "Categorizing transactions using API at: $API_URL"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_size": 10
  }'
