#!/bin/bash
set -e

LOCAL_DB="postgresql://postgres:postgres@localhost:54321/bank_statements"
DUMP_FILE="/tmp/db_sync_dump.sql"

usage() {
    echo "Usage: $0 <direction>"
    echo ""
    echo "Directions:"
    echo "  neon-to-local    Dump Neon DB and restore to local"
    echo "  local-to-neon    Dump local DB and restore to Neon"
    echo ""
    echo "Neon connection string must be provided via:"
    echo "  - NEON_DATABASE_URL environment variable, or"
    echo "  - Clipboard (will prompt to confirm)"
    echo ""
    echo "Examples:"
    echo "  NEON_DATABASE_URL='postgresql://...' $0 neon-to-local"
    echo "  $0 local-to-neon  # uses clipboard"
    exit 1
}

get_neon_url() {
    if [ -n "$NEON_DATABASE_URL" ]; then
        echo "$NEON_DATABASE_URL"
        return
    fi

    if command -v pbpaste &> /dev/null; then
        CLIPBOARD=$(pbpaste)
    elif command -v xclip &> /dev/null; then
        CLIPBOARD=$(xclip -selection clipboard -o)
    else
        echo "Error: No clipboard tool found and NEON_DATABASE_URL not set" >&2
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

neon_to_local() {
    NEON_URL=$(get_neon_url)

    echo "==> Dumping Neon database..."
    pg_dump "$NEON_URL" --no-owner --no-acl -F p > "$DUMP_FILE"

    echo "==> Restoring to local database..."
    psql "$LOCAL_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>/dev/null || true
    psql "$LOCAL_DB" < "$DUMP_FILE"

    rm -f "$DUMP_FILE"
    echo "==> Done! Local database synced from Neon."
}

local_to_neon() {
    NEON_URL=$(get_neon_url)

    echo "==> Dumping local database..."
    pg_dump "$LOCAL_DB" --no-owner --no-acl -F p > "$DUMP_FILE"

    echo "==> Restoring to Neon database..."
    psql "$NEON_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>/dev/null || true
    psql "$NEON_URL" < "$DUMP_FILE"

    rm -f "$DUMP_FILE"
    echo "==> Done! Neon database synced from local."
    echo ""
    echo "NOTE: You may need to redeploy on Render to run migrations."
}

case "${1:-}" in
    neon-to-local)
        neon_to_local
        ;;
    local-to-neon)
        local_to_neon
        ;;
    *)
        usage
        ;;
esac
