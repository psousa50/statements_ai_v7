#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/bank_statements_20240101_120000.dump"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Error: File not found: $1"
    exit 1
fi

docker exec -i bank-statements-db pg_restore -U postgres -d bank_statements -c < "$1"
echo "Restored from: $1"
