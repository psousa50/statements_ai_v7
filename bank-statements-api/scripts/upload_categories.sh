#!/bin/bash

# Default file path
CSV_FILE="${1:-../data/categories.csv}"
API_URL="${API_BASE_URL:-http://localhost:8000}/api/v1/categories/upload"

echo "Uploading categories from: $CSV_FILE"
echo "Using API at: $API_URL"

# Check if file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: CSV file not found at $CSV_FILE"
    echo "Usage: $0 [csv_file_path]"
    echo ""
    echo "CSV file should contain two columns: parent_name, name"
    echo "Example:"
    echo "parent_name,name"
    echo ",Food"
    echo "Food,Groceries"
    echo "Food,Restaurants"
    exit 1
fi

# Upload the file using multipart form data
curl -X POST "$API_URL" \
  -F "file=@$CSV_FILE" \
  -H "Accept: application/json"