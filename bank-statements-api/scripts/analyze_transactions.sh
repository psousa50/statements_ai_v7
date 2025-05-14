#!/bin/bash

FILE=$1
API_URL="http://localhost:8000/api/v1/statements/analyze"

if [ -z "$FILE" ]; then
  FILE="/Users/pedrosousa/Work/Personal/statements/tmp/revolut_some.csv"
fi

if [ ! -f "$FILE" ]; then
  echo "File not found: $FILE"
  exit 1
fi

curl -X POST "$API_URL" \
  -F "file=@$FILE"