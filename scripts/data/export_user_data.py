#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import psycopg


def get_user_id(conn, user_identifier: str) -> UUID | None:
    with conn.cursor() as cur:
        try:
            user_uuid = UUID(user_identifier)
            cur.execute("SELECT id FROM users WHERE id = %s", (user_uuid,))
        except ValueError:
            cur.execute("SELECT id FROM users WHERE email = %s", (user_identifier,))
        row = cur.fetchone()
        return row[0] if row else None


def create_sqlite_schema(sqlite_conn):
    sqlite_conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            currency TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT,
            parent_id TEXT
        );

        CREATE TABLE IF NOT EXISTS statements (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            content BLOB NOT NULL,
            transaction_count INTEGER,
            date_from TEXT,
            date_to TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS initial_balances (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            balance_date TEXT NOT NULL,
            balance_amount TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS file_analysis_metadata (
            id TEXT PRIMARY KEY,
            file_hash TEXT NOT NULL,
            account_id TEXT NOT NULL,
            column_mapping TEXT NOT NULL,
            header_row_index INTEGER NOT NULL,
            data_start_row_index INTEGER NOT NULL,
            row_filters TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            normalized_description TEXT NOT NULL,
            amount TEXT NOT NULL,
            created_at TEXT NOT NULL,
            statement_id TEXT NOT NULL,
            category_id TEXT,
            account_id TEXT NOT NULL,
            counterparty_account_id TEXT,
            categorization_status TEXT NOT NULL,
            categorization_confidence TEXT,
            counterparty_status TEXT NOT NULL,
            row_index INTEGER NOT NULL,
            sort_index INTEGER NOT NULL,
            source_type TEXT NOT NULL,
            manual_position_after TEXT
        );

        CREATE TABLE IF NOT EXISTS enhancement_rules (
            id TEXT PRIMARY KEY,
            normalized_description_pattern TEXT NOT NULL,
            match_type TEXT NOT NULL,
            min_amount TEXT,
            max_amount TEXT,
            start_date TEXT,
            end_date TEXT,
            category_id TEXT,
            counterparty_account_id TEXT,
            ai_suggested_category_id TEXT,
            ai_category_confidence TEXT,
            ai_suggested_counterparty_id TEXT,
            ai_counterparty_confidence TEXT,
            ai_processed_at TEXT,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS description_groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS description_group_members (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            normalized_description TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS saved_filters (
            id TEXT PRIMARY KEY,
            filter_data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)


def serialize_value(val):
    if val is None:
        return None
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, dict):
        return json.dumps(val)
    if isinstance(val, bytes):
        return val
    return val


def export_accounts(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, currency FROM accounts WHERE user_id = %s",
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            "INSERT INTO accounts (id, name, currency) VALUES (?, ?, ?)",
            (str(row[0]), row[1], row[2]),
        )
    return len(rows)


def export_categories(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, color, parent_id FROM categories WHERE user_id = %s",
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            "INSERT INTO categories (id, name, color, parent_id) VALUES (?, ?, ?, ?)",
            (str(row[0]), row[1], row[2], str(row[3]) if row[3] else None),
        )
    return len(rows)


def export_statements(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.account_id, s.filename, s.file_type, s.content,
                   s.transaction_count, s.date_from, s.date_to, s.created_at
            FROM statements s
            JOIN accounts a ON s.account_id = a.id
            WHERE a.user_id = %s
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            """INSERT INTO statements
               (id, account_id, filename, file_type, content, transaction_count,
                date_from, date_to, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(row[0]),
                str(row[1]),
                row[2],
                row[3],
                row[4],
                row[5],
                serialize_value(row[6]),
                serialize_value(row[7]),
                serialize_value(row[8]),
            ),
        )
    return len(rows)


def export_initial_balances(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT ib.id, ib.account_id, ib.balance_date, ib.balance_amount,
                   ib.created_at, ib.updated_at
            FROM initial_balances ib
            JOIN accounts a ON ib.account_id = a.id
            WHERE a.user_id = %s
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            """INSERT INTO initial_balances
               (id, account_id, balance_date, balance_amount, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(row[0]),
                str(row[1]),
                serialize_value(row[2]),
                serialize_value(row[3]),
                serialize_value(row[4]),
                serialize_value(row[5]),
            ),
        )
    return len(rows)


def export_file_analysis_metadata(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT fam.id, fam.file_hash, fam.account_id, fam.column_mapping,
                   fam.header_row_index, fam.data_start_row_index, fam.row_filters,
                   fam.created_at
            FROM file_analysis_metadata fam
            JOIN accounts a ON fam.account_id = a.id
            WHERE a.user_id = %s
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            """INSERT INTO file_analysis_metadata
               (id, file_hash, account_id, column_mapping, header_row_index,
                data_start_row_index, row_filters, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(row[0]),
                row[1],
                str(row[2]),
                json.dumps(row[3]) if row[3] else None,
                row[4],
                row[5],
                json.dumps(row[6]) if row[6] else None,
                serialize_value(row[7]),
            ),
        )
    return len(rows)


def export_transactions(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, date, description, normalized_description, amount, created_at,
                   statement_id, category_id, account_id, counterparty_account_id,
                   categorization_status, categorization_confidence, counterparty_status,
                   row_index, sort_index, source_type, manual_position_after
            FROM transactions
            WHERE user_id = %s
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            """INSERT INTO transactions
               (id, date, description, normalized_description, amount, created_at,
                statement_id, category_id, account_id, counterparty_account_id,
                categorization_status, categorization_confidence, counterparty_status,
                row_index, sort_index, source_type, manual_position_after)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(row[0]),
                serialize_value(row[1]),
                row[2],
                row[3],
                serialize_value(row[4]),
                serialize_value(row[5]),
                str(row[6]),
                str(row[7]) if row[7] else None,
                str(row[8]),
                str(row[9]) if row[9] else None,
                row[10],
                serialize_value(row[11]),
                row[12],
                row[13],
                row[14],
                row[15],
                str(row[16]) if row[16] else None,
            ),
        )
    return len(rows)


def export_enhancement_rules(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, normalized_description_pattern, match_type, min_amount, max_amount,
                   start_date, end_date, category_id, counterparty_account_id,
                   ai_suggested_category_id, ai_category_confidence,
                   ai_suggested_counterparty_id, ai_counterparty_confidence,
                   ai_processed_at, source, created_at, updated_at
            FROM enhancement_rules
            WHERE user_id = %s
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            """INSERT INTO enhancement_rules
               (id, normalized_description_pattern, match_type, min_amount, max_amount,
                start_date, end_date, category_id, counterparty_account_id,
                ai_suggested_category_id, ai_category_confidence,
                ai_suggested_counterparty_id, ai_counterparty_confidence,
                ai_processed_at, source, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(row[0]),
                row[1],
                row[2],
                serialize_value(row[3]),
                serialize_value(row[4]),
                serialize_value(row[5]),
                serialize_value(row[6]),
                str(row[7]) if row[7] else None,
                str(row[8]) if row[8] else None,
                str(row[9]) if row[9] else None,
                serialize_value(row[10]),
                str(row[11]) if row[11] else None,
                serialize_value(row[12]),
                serialize_value(row[13]),
                row[14],
                serialize_value(row[15]),
                serialize_value(row[16]),
            ),
        )
    return len(rows)


def export_description_groups(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, created_at, updated_at FROM description_groups WHERE user_id = %s",
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            "INSERT INTO description_groups (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (str(row[0]), row[1], serialize_value(row[2]), serialize_value(row[3])),
        )
    return len(rows)


def export_description_group_members(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT dgm.id, dgm.group_id, dgm.normalized_description, dgm.created_at
            FROM description_group_members dgm
            JOIN description_groups dg ON dgm.group_id = dg.id
            WHERE dg.user_id = %s
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            """INSERT INTO description_group_members
               (id, group_id, normalized_description, created_at)
               VALUES (?, ?, ?, ?)""",
            (str(row[0]), str(row[1]), row[2], serialize_value(row[3])),
        )
    return len(rows)


def export_saved_filters(pg_conn, sqlite_conn, user_id: UUID) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT id, filter_data, created_at, expires_at FROM saved_filters WHERE user_id = %s",
            (user_id,),
        )
        rows = cur.fetchall()

    for row in rows:
        sqlite_conn.execute(
            "INSERT INTO saved_filters (id, filter_data, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (
                str(row[0]),
                json.dumps(row[1]) if row[1] else None,
                serialize_value(row[2]),
                serialize_value(row[3]),
            ),
        )
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Export user data to SQLite file")
    parser.add_argument("--user", required=True, help="User email or UUID to export")
    parser.add_argument("--output", required=True, help="Output SQLite file path")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    database_url = database_url.replace("postgresql+psycopg://", "postgresql://")

    output_path = Path(args.output)
    if output_path.exists():
        print(f"ERROR: Output file already exists: {output_path}")
        sys.exit(1)

    print("=" * 60)
    print("USER DATA EXPORT")
    print("=" * 60)
    print()

    print("Connecting to database...")
    pg_conn = psycopg.connect(database_url)
    print("  Connected successfully")

    print(f"Looking up user: {args.user}")
    user_id = get_user_id(pg_conn, args.user)
    if not user_id:
        print(f"  ERROR: User not found: {args.user}")
        pg_conn.close()
        sys.exit(1)
    print(f"  Found user: {user_id}")
    print()

    print(f"Creating export file: {output_path}")
    sqlite_conn = sqlite3.connect(output_path)
    create_sqlite_schema(sqlite_conn)

    sqlite_conn.execute(
        "INSERT INTO metadata (key, value) VALUES (?, ?)",
        ("source_user_id", str(user_id)),
    )
    sqlite_conn.execute(
        "INSERT INTO metadata (key, value) VALUES (?, ?)",
        ("exported_at", datetime.now().isoformat()),
    )
    print()

    print("Exporting data...")
    counts = {}

    counts["accounts"] = export_accounts(pg_conn, sqlite_conn, user_id)
    print(f"  Accounts: {counts['accounts']}")

    counts["categories"] = export_categories(pg_conn, sqlite_conn, user_id)
    print(f"  Categories: {counts['categories']}")

    counts["statements"] = export_statements(pg_conn, sqlite_conn, user_id)
    print(f"  Statements: {counts['statements']}")

    counts["initial_balances"] = export_initial_balances(pg_conn, sqlite_conn, user_id)
    print(f"  Initial balances: {counts['initial_balances']}")

    counts["file_analysis_metadata"] = export_file_analysis_metadata(pg_conn, sqlite_conn, user_id)
    print(f"  File analysis metadata: {counts['file_analysis_metadata']}")

    counts["transactions"] = export_transactions(pg_conn, sqlite_conn, user_id)
    print(f"  Transactions: {counts['transactions']}")

    counts["enhancement_rules"] = export_enhancement_rules(pg_conn, sqlite_conn, user_id)
    print(f"  Enhancement rules: {counts['enhancement_rules']}")

    counts["description_groups"] = export_description_groups(pg_conn, sqlite_conn, user_id)
    print(f"  Description groups: {counts['description_groups']}")

    counts["description_group_members"] = export_description_group_members(pg_conn, sqlite_conn, user_id)
    print(f"  Description group members: {counts['description_group_members']}")

    counts["saved_filters"] = export_saved_filters(pg_conn, sqlite_conn, user_id)
    print(f"  Saved filters: {counts['saved_filters']}")

    sqlite_conn.commit()
    sqlite_conn.close()
    pg_conn.close()

    print()
    print("=" * 60)
    print(f"EXPORT COMPLETE: {output_path}")
    print(f"Total records: {sum(counts.values())}")
    print("=" * 60)


if __name__ == "__main__":
    main()
