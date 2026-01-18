#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
BACKUP_DIR="$ROOT_DIR/backups"

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/bank_statements_$(date +%Y%m%d_%H%M%S).dump"

docker exec bank-statements-db pg_dump -U postgres -d bank_statements -F c > "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"
