#!/bin/bash

API_URL="http://localhost:8000/api/v1/transactions/categorize-batch"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
