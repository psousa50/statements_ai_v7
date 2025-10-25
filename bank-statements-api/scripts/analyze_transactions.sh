#!/bin/bash

API_URL="${API_BASE_URL:-http://localhost:8010}/api/v1/statements/analyze"

FILE_PATH="${1:-./data/statements/100_BT_Records.csv}"

if [ ! -f "$FILE_PATH" ]; then
  echo "Error: File not found: $FILE_PATH"
  echo "Usage: $0 [file_path]"
  exit 1
fi

echo "Analyzing file: $FILE_PATH"
echo "Using API at: $API_URL"
echo ""

curl -X POST "$API_URL" \
  -F "file=@$FILE_PATH"
