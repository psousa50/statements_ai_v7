#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
import sys
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Json


def get_user_id(conn, user_identifier: str) -> UUID | None:
    with conn.cursor() as cur:
        try:
            user_uuid = UUID(user_identifier)
            cur.execute("SELECT id FROM users WHERE id = %s", (user_uuid,))
        except ValueError:
            cur.execute("SELECT id FROM users WHERE email = %s", (user_identifier,))
        row = cur.fetchone()
        return row[0] if row else None


def check_user_has_data(conn, user_id: UUID) -> dict[str, int]:
    counts = {}
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM accounts WHERE user_id = %s", (user_id,))
        counts["accounts"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM categories WHERE user_id = %s", (user_id,))
        counts["categories"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions WHERE user_id = %s", (user_id,))
        counts["transactions"] = cur.fetchone()[0]
    return counts


def parse_date(val: str | None) -> date | None:
    if not val:
        return None
    return date.fromisoformat(val[:10])


def parse_datetime(val: str | None) -> datetime | None:
    if not val:
        return None
    if val.endswith("Z"):
        val = val[:-1] + "+00:00"
    return datetime.fromisoformat(val)


def parse_decimal(val: str | None) -> Decimal | None:
    if not val:
        return None
    return Decimal(val)


def parse_json(val: str | None) -> Json | None:
    if not val:
        return None
    return Json(json.loads(val))


def remap_id(id_map: dict[str, UUID], old_id: str | None) -> UUID | None:
    if not old_id:
        return None
    return id_map.get(old_id)


def import_accounts(sqlite_conn, pg_conn, user_id: UUID) -> dict[str, UUID]:
    cursor = sqlite_conn.execute("SELECT id, name, currency FROM accounts")
    rows = cursor.fetchall()

    id_map = {}
    with pg_conn.cursor() as cur:
        for row in rows:
            old_id, name, currency = row
            new_id = uuid4()
            id_map[old_id] = new_id
            cur.execute(
                "INSERT INTO accounts (id, user_id, name, currency) VALUES (%s, %s, %s, %s)",
                (new_id, user_id, name, currency),
            )
    return id_map


def import_categories(sqlite_conn, pg_conn, user_id: UUID) -> dict[str, UUID]:
    cursor = sqlite_conn.execute("SELECT id, name, color, parent_id FROM categories")
    rows = cursor.fetchall()

    id_map = {}
    for row in rows:
        old_id = row[0]
        id_map[old_id] = uuid4()

    parents_first = sorted(rows, key=lambda r: (r[3] is not None, r[3] or ""))

    with pg_conn.cursor() as cur:
        for row in parents_first:
            old_id, name, color, old_parent_id = row
            new_id = id_map[old_id]
            new_parent_id = remap_id(id_map, old_parent_id)
            cur.execute(
                "INSERT INTO categories (id, user_id, name, color, parent_id) VALUES (%s, %s, %s, %s, %s)",
                (new_id, user_id, name, color, new_parent_id),
            )
    return id_map


def import_statements(sqlite_conn, pg_conn, account_map: dict[str, UUID]) -> dict[str, UUID]:
    cursor = sqlite_conn.execute(
        """SELECT id, account_id, filename, file_type, content,
                  transaction_count, date_from, date_to, created_at
           FROM statements"""
    )
    rows = cursor.fetchall()

    id_map = {}
    with pg_conn.cursor() as cur:
        for row in rows:
            old_id = row[0]
            new_id = uuid4()
            id_map[old_id] = new_id

            new_account_id = remap_id(account_map, row[1])
            if not new_account_id:
                continue

            cur.execute(
                """INSERT INTO statements
                   (id, account_id, filename, file_type, content,
                    transaction_count, date_from, date_to, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    new_id,
                    new_account_id,
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    parse_date(row[6]),
                    parse_date(row[7]),
                    parse_datetime(row[8]),
                ),
            )
    return id_map


def import_initial_balances(sqlite_conn, pg_conn, account_map: dict[str, UUID]) -> int:
    cursor = sqlite_conn.execute(
        """SELECT id, account_id, balance_date, balance_amount, created_at, updated_at
           FROM initial_balances"""
    )
    rows = cursor.fetchall()

    count = 0
    with pg_conn.cursor() as cur:
        for row in rows:
            new_account_id = remap_id(account_map, row[1])
            if not new_account_id:
                continue

            cur.execute(
                """INSERT INTO initial_balances
                   (id, account_id, balance_date, balance_amount, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    uuid4(),
                    new_account_id,
                    parse_date(row[2]),
                    parse_decimal(row[3]),
                    parse_datetime(row[4]),
                    parse_datetime(row[5]),
                ),
            )
            count += 1
    return count


def import_file_analysis_metadata(sqlite_conn, pg_conn, account_map: dict[str, UUID]) -> int:
    cursor = sqlite_conn.execute(
        """SELECT id, file_hash, account_id, column_mapping, header_row_index,
                  data_start_row_index, row_filters, created_at
           FROM file_analysis_metadata"""
    )
    rows = cursor.fetchall()

    count = 0
    with pg_conn.cursor() as cur:
        for row in rows:
            new_account_id = remap_id(account_map, row[2])
            if not new_account_id:
                continue

            cur.execute(
                """INSERT INTO file_analysis_metadata
                   (id, file_hash, account_id, column_mapping, header_row_index,
                    data_start_row_index, row_filters, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    uuid4(),
                    row[1],
                    new_account_id,
                    parse_json(row[3]),
                    row[4],
                    row[5],
                    parse_json(row[6]),
                    parse_datetime(row[7]),
                ),
            )
            count += 1
    return count


def import_transactions(
    sqlite_conn,
    pg_conn,
    user_id: UUID,
    account_map: dict[str, UUID],
    category_map: dict[str, UUID],
    statement_map: dict[str, UUID],
) -> dict[str, UUID]:
    cursor = sqlite_conn.execute(
        """SELECT id, date, description, normalized_description, amount, created_at,
                  statement_id, category_id, account_id, counterparty_account_id,
                  categorization_status, categorization_confidence, counterparty_status,
                  row_index, sort_index, source_type, manual_position_after
           FROM transactions"""
    )
    rows = cursor.fetchall()

    id_map = {}
    for row in rows:
        id_map[row[0]] = uuid4()

    with pg_conn.cursor() as cur:
        for row in rows:
            old_id = row[0]
            new_id = id_map[old_id]

            new_account_id = remap_id(account_map, row[8])
            new_statement_id = remap_id(statement_map, row[6])
            if not new_account_id or not new_statement_id:
                continue

            cur.execute(
                """INSERT INTO transactions
                   (id, user_id, date, description, normalized_description, amount, created_at,
                    statement_id, category_id, account_id, counterparty_account_id,
                    categorization_status, categorization_confidence, counterparty_status,
                    row_index, sort_index, source_type, manual_position_after)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    new_id,
                    user_id,
                    parse_date(row[1]),
                    row[2],
                    row[3],
                    parse_decimal(row[4]),
                    parse_datetime(row[5]),
                    new_statement_id,
                    remap_id(category_map, row[7]),
                    new_account_id,
                    remap_id(account_map, row[9]),
                    row[10],
                    parse_decimal(row[11]),
                    row[12],
                    row[13],
                    row[14],
                    row[15],
                    remap_id(id_map, row[16]),
                ),
            )
    return id_map


def import_enhancement_rules(
    sqlite_conn,
    pg_conn,
    user_id: UUID,
    account_map: dict[str, UUID],
    category_map: dict[str, UUID],
) -> int:
    cursor = sqlite_conn.execute(
        """SELECT id, normalized_description_pattern, match_type, min_amount, max_amount,
                  start_date, end_date, category_id, counterparty_account_id,
                  ai_suggested_category_id, ai_category_confidence,
                  ai_suggested_counterparty_id, ai_counterparty_confidence,
                  ai_processed_at, source, created_at, updated_at
           FROM enhancement_rules"""
    )
    rows = cursor.fetchall()

    count = 0
    with pg_conn.cursor() as cur:
        for row in rows:
            cur.execute(
                """INSERT INTO enhancement_rules
                   (id, user_id, normalized_description_pattern, match_type, min_amount, max_amount,
                    start_date, end_date, category_id, counterparty_account_id,
                    ai_suggested_category_id, ai_category_confidence,
                    ai_suggested_counterparty_id, ai_counterparty_confidence,
                    ai_processed_at, source, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    uuid4(),
                    user_id,
                    row[1],
                    row[2],
                    parse_decimal(row[3]),
                    parse_decimal(row[4]),
                    parse_date(row[5]),
                    parse_date(row[6]),
                    remap_id(category_map, row[7]),
                    remap_id(account_map, row[8]),
                    remap_id(category_map, row[9]),
                    parse_decimal(row[10]),
                    remap_id(account_map, row[11]),
                    parse_decimal(row[12]),
                    parse_datetime(row[13]),
                    row[14],
                    parse_datetime(row[15]),
                    parse_datetime(row[16]),
                ),
            )
            count += 1
    return count


def import_description_groups(sqlite_conn, pg_conn, user_id: UUID) -> dict[str, UUID]:
    cursor = sqlite_conn.execute(
        "SELECT id, name, created_at, updated_at FROM description_groups"
    )
    rows = cursor.fetchall()

    id_map = {}
    with pg_conn.cursor() as cur:
        for row in rows:
            old_id, name, created_at, updated_at = row
            new_id = uuid4()
            id_map[old_id] = new_id
            cur.execute(
                """INSERT INTO description_groups (id, user_id, name, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (new_id, user_id, name, parse_datetime(created_at), parse_datetime(updated_at)),
            )
    return id_map


def import_description_group_members(
    sqlite_conn, pg_conn, group_map: dict[str, UUID]
) -> int:
    cursor = sqlite_conn.execute(
        "SELECT id, group_id, normalized_description, created_at FROM description_group_members"
    )
    rows = cursor.fetchall()

    count = 0
    with pg_conn.cursor() as cur:
        for row in rows:
            new_group_id = remap_id(group_map, row[1])
            if not new_group_id:
                continue

            cur.execute(
                """INSERT INTO description_group_members
                   (id, group_id, normalized_description, created_at)
                   VALUES (%s, %s, %s, %s)""",
                (uuid4(), new_group_id, row[2], parse_datetime(row[3])),
            )
            count += 1
    return count


def import_saved_filters(sqlite_conn, pg_conn, user_id: UUID) -> int:
    cursor = sqlite_conn.execute(
        "SELECT id, filter_data, created_at, expires_at FROM saved_filters"
    )
    rows = cursor.fetchall()

    count = 0
    with pg_conn.cursor() as cur:
        for row in rows:
            cur.execute(
                """INSERT INTO saved_filters (id, user_id, filter_data, created_at, expires_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    uuid4(),
                    user_id,
                    parse_json(row[1]),
                    parse_datetime(row[2]),
                    parse_datetime(row[3]),
                ),
            )
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Import user data from SQLite file")
    parser.add_argument("--input", required=True, help="Input SQLite file path")
    parser.add_argument("--user", required=True, help="Target user email or UUID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without making changes")
    parser.add_argument("--force", action="store_true", help="Allow import even if target user has existing data")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    database_url = database_url.replace("postgresql+psycopg://", "postgresql://")

    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    print("=" * 60)
    print("USER DATA IMPORT")
    print("=" * 60)
    if args.dry_run:
        print("MODE: DRY RUN (no changes will be made)")
    print()

    print(f"Opening export file: {args.input}")
    sqlite_conn = sqlite3.connect(args.input)

    cursor = sqlite_conn.execute("SELECT key, value FROM metadata")
    metadata = dict(cursor.fetchall())
    print(f"  Source user: {metadata.get('source_user_id', 'unknown')}")
    print(f"  Exported at: {metadata.get('exported_at', 'unknown')}")
    print()

    print("Connecting to database...")
    pg_conn = psycopg.connect(database_url)
    print("  Connected successfully")

    print(f"Looking up target user: {args.user}")
    user_id = get_user_id(pg_conn, args.user)
    if not user_id:
        print(f"  ERROR: User not found: {args.user}")
        pg_conn.close()
        sqlite_conn.close()
        sys.exit(1)
    print(f"  Found user: {user_id}")

    existing_data = check_user_has_data(pg_conn, user_id)
    total_existing = sum(existing_data.values())
    if total_existing > 0 and not args.force:
        print()
        print("  ERROR: Target user already has data:")
        for table, count in existing_data.items():
            if count > 0:
                print(f"    {table}: {count}")
        print()
        print("  Use --force to import anyway (data will be merged)")
        pg_conn.close()
        sqlite_conn.close()
        sys.exit(1)
    print()

    counts = {}

    def count_rows(table: str) -> int:
        cursor = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]

    print("Data to import:")
    for table in [
        "accounts",
        "categories",
        "statements",
        "initial_balances",
        "file_analysis_metadata",
        "transactions",
        "enhancement_rules",
        "description_groups",
        "description_group_members",
        "saved_filters",
    ]:
        counts[table] = count_rows(table)
        print(f"  {table}: {counts[table]}")
    print()

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN COMPLETE - No changes made")
        print(f"Would import {sum(counts.values())} records")
        print("=" * 60)
        pg_conn.close()
        sqlite_conn.close()
        return

    print("Importing data...")

    account_map = import_accounts(sqlite_conn, pg_conn, user_id)
    print(f"  Accounts: {len(account_map)}")

    category_map = import_categories(sqlite_conn, pg_conn, user_id)
    print(f"  Categories: {len(category_map)}")

    statement_map = import_statements(sqlite_conn, pg_conn, account_map)
    print(f"  Statements: {len(statement_map)}")

    ib_count = import_initial_balances(sqlite_conn, pg_conn, account_map)
    print(f"  Initial balances: {ib_count}")

    fam_count = import_file_analysis_metadata(sqlite_conn, pg_conn, account_map)
    print(f"  File analysis metadata: {fam_count}")

    txn_map = import_transactions(
        sqlite_conn, pg_conn, user_id, account_map, category_map, statement_map
    )
    print(f"  Transactions: {len(txn_map)}")

    rule_count = import_enhancement_rules(
        sqlite_conn, pg_conn, user_id, account_map, category_map
    )
    print(f"  Enhancement rules: {rule_count}")

    group_map = import_description_groups(sqlite_conn, pg_conn, user_id)
    print(f"  Description groups: {len(group_map)}")

    member_count = import_description_group_members(sqlite_conn, pg_conn, group_map)
    print(f"  Description group members: {member_count}")

    filter_count = import_saved_filters(sqlite_conn, pg_conn, user_id)
    print(f"  Saved filters: {filter_count}")

    pg_conn.commit()
    pg_conn.close()
    sqlite_conn.close()

    print()
    print("=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
