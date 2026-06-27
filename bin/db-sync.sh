#!/bin/bash
set -e

LOCAL_DB="postgresql://postgres:postgres@localhost:54321/bank_statements"
DUMP_FILE="/tmp/db_sync_dump.sql"

usage() {
    echo "Usage: $0 <direction>"
    echo ""
    echo "Directions:"
    echo "  from-remote    Dump remote DB and restore to local"
    echo ""
    echo "Remote connection string must be provided via:"
    echo "  - REMOTE_DATABASE_URL environment variable, or"
    echo "  - Clipboard (will prompt to confirm)"
    echo ""
    echo "Examples:"
    echo "  REMOTE_DATABASE_URL='postgresql://...' $0 from-remote"
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

    if [[ ! "$CLIPBOARD" =~ ^postgres(ql)?:// ]]; then
        echo "Error: Clipboard doesn't contain a valid PostgreSQL URL" >&2
        echo "Clipboard content starts with: ${CLIPBOARD:0:30}..." >&2
        exit 1
    fi

    MASKED_URL=$(echo "$CLIPBOARD" | sed 's/:[^:@]*@/:****@/')
    echo "Found in clipboard: $MASKED_URL" >&2
    read -p "Use this connection string? [y/N] " -n 1 -r
    echo >&2
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted" >&2
        exit 1
    fi

    echo "$CLIPBOARD"
}

from_remote() {
    REMOTE_URL=$(get_remote_url)

    echo "==> Dumping remote database..."
    pg_dump "$REMOTE_URL" --no-owner --no-acl -F p > "$DUMP_FILE"

    echo "==> Restoring to local database..."
    psql "$LOCAL_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>/dev/null || true
    psql "$LOCAL_DB" < "$DUMP_FILE"

    rm -f "$DUMP_FILE"
    echo "==> Done! Local database synced from remote."
}

case "${1:-}" in
    from-remote)
        from_remote
        ;;
    *)
        usage
        ;;
esac
