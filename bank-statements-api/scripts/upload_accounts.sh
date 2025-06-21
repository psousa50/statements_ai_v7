#!/bin/bash

# Default file path
CSV_FILE="${1:-../data/accounts.csv}"
API_URL="${API_BASE_URL:-http://localhost:8000}/api/v1/accounts/upload"

echo "Uploading accounts from: $CSV_FILE"
echo "Using API at: $API_URL"

# Check if file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: CSV file not found at $CSV_FILE"
    echo "Usage: $0 [csv_file_path]"
    exit 1
fi

# Upload the file using multipart form data
curl -X POST "$API_URL" \
  -F "file=@$CSV_FILE" \
  -H "Accept: application/json"
