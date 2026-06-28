#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
BACKUP_DIR="$ROOT_DIR/backups"

usage() {
    echo "Usage: $0"
    echo ""
    echo "Dumps the remote (production) database to $BACKUP_DIR."
    echo ""
    echo "Remote connection string must be provided via:"
    echo "  - REMOTE_DATABASE_URL environment variable, or"
    echo "  - Clipboard (will prompt to confirm)"
    exit 1
}

get_remote_url() {
    if [ -n "$REMOTE_DATABASE_URL" ]; then
        echo "$REMOTE_DATABASE_URL"
        return
    fi

    if command -v pbpaste &> /dev/null; then
        CLIPBOARD=$(pbpaste)
    elif command -v xclip &> /dev/null; then
        CLIPBOARD=$(xclip -selection clipboard -o)
    else
        echo "Error: No clipboard tool found and REMOTE_DATABASE_URL not set" >&2
        exit 1
    fi

    CLIPBOARD=$(echo "$CLIPBOARD" | sed -E 's#^(postgres(ql)?)\+[a-z0-9]+://#\1://#')

    if [[ ! "$CLIPBOARD" =~ ^postgres(ql)?:// ]]; then
        echo "Error: Clipboard doesn't contain a valid PostgreSQL URL" >&2
        echo "Clipboard content starts with: ${CLIPBOARD:0:30}..." >&2
        exit 1
    fi

    MASKED_URL=$(echo "$CLIPBOARD" | sed 's/:[^:@]*@/:****@/')
    echo "Found in clipboard: $MASKED_URL" >&2
    read -p "Back up THIS database? [y/N] " -n 1 -r
    echo >&2
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted" >&2
        exit 1
    fi

    echo "$CLIPBOARD"
}

[ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] && usage

REMOTE_URL=$(get_remote_url)

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/bank_statements_prod_$(date +%Y%m%d_%H%M%S).dump"

echo "==> Dumping remote database..."
pg_dump "$REMOTE_URL" --no-owner --no-acl -F c > "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"
echo "Restore with: pg_restore --no-owner --no-acl -d <target-url> \"$BACKUP_FILE\""
