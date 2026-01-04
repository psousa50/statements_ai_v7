#!/usr/bin/env python3
import argparse
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import psycopg


def normalize_description(description: str) -> str:
    if not description:
        return ""
    text = description.lower()
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = re.sub(
        r"\b(ref|reference|#|id|date)\b[:\s]*[\w\d\-\/\.]+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", "", text)
    text = re.sub(r"\bon\s+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", "", text)
    text = re.sub(r"[^a-z\s]", "", text)
    words_to_remove = ["id", "ref", "on", "at", "to", "from", "the", "and", "for"]
    for word in words_to_remove:
        text = re.sub(r"\b" + word + r"\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_amount(val) -> Decimal | None:
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    val_str = str(val).strip()
    cleaned = re.sub(r"[^\d,.\-]", "", val_str)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def parse_date(val) -> str | None:
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if len(val_str) >= 10 and val_str[4] == "-":
        return val_str[:10]
    for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(val_str[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def detect_csv_format(df: pd.DataFrame) -> dict | None:
    cols = [c.lower().strip() for c in df.columns]
    if "date" in cols and "description" in cols and "amount" in cols:
        return {"date": "Date", "description": "Description", "amount": "Amount", "type": "simple"}
    if "data lanc." in cols or "data valor" in cols:
        date_col = "Data Lanc." if "Data Lanc." in df.columns else df.columns[0]
        desc_col = "Descrição" if "Descrição" in df.columns else df.columns[2]
        amount_col = "Valor" if "Valor" in df.columns else df.columns[3]
        return {"date": date_col, "description": desc_col, "amount": amount_col, "type": "ab7"}
    if "data de início" in cols or "data de conclusão" in cols:
        date_col = "Data de Conclusão" if "Data de Conclusão" in df.columns else df.columns[3]
        desc_col = "Descrição" if "Descrição" in df.columns else df.columns[4]
        amount_col = "Montante" if "Montante" in df.columns else df.columns[5]
        return {"date": date_col, "description": desc_col, "amount": amount_col, "type": "revolut"}
    return None


def parse_csv_file(filepath: Path) -> list[tuple[str, str, Decimal]]:
    try:
        df = pd.read_csv(filepath, dtype=str)
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return []

    mapping = detect_csv_format(df)
    if not mapping:
        print(f"  Unknown format: {filepath}")
        return []

    transactions = []
    for _, row in df.iterrows():
        date = parse_date(row.get(mapping["date"]))
        desc = str(row.get(mapping["description"], ""))
        amount = parse_amount(row.get(mapping["amount"]))

        if date and amount is not None:
            norm_desc = normalize_description(desc)
            transactions.append((date, norm_desc, amount))

    return transactions


def get_csv_counts(csv_dir: Path, exclude_patterns: list[str] = None) -> dict[tuple[str, str, Decimal], int]:
    csv_files = list(csv_dir.glob("**/*.csv"))
    csv_files = [f for f in csv_files if "tests" not in str(f)]

    if exclude_patterns:
        for pattern in exclude_patterns:
            csv_files = [f for f in csv_files if pattern.lower() not in f.name.lower()]

    print(f"Found {len(csv_files)} CSV files to process")

    # For each file, count transactions per key
    # Then for overlapping days, take the max count from any single file
    file_counts = []
    all_dates_per_file = []

    for filepath in csv_files:
        print(f"  Processing: {filepath.name}")
        transactions = parse_csv_file(filepath)
        counts = defaultdict(int)
        dates = set()
        for key in transactions:
            counts[key] += 1
            dates.add(key[0])  # date is first element
        file_counts.append(dict(counts))
        all_dates_per_file.append(dates)
        print(f"    -> {len(transactions)} transactions, dates: {min(dates) if dates else 'none'} to {max(dates) if dates else 'none'}")

    # Merge counts: for each key, take max count from any file that covers that date
    # This handles overlapping CSVs correctly
    merged_counts = defaultdict(int)
    all_keys = set()
    for fc in file_counts:
        all_keys.update(fc.keys())

    for key in all_keys:
        date = key[0]
        max_count = 0
        for i, fc in enumerate(file_counts):
            if date in all_dates_per_file[i]:
                # This file covers this date, use its count (0 if key not present)
                count = fc.get(key, 0)
                max_count = max(max_count, count)
        merged_counts[key] = max_count

    return dict(merged_counts)


def get_db_counts(conn) -> dict[tuple[str, str, Decimal], int]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT date::text, normalized_description, amount, COUNT(*) as cnt
            FROM transactions
            GROUP BY date, normalized_description, amount
        """)
        rows = cur.fetchall()

    counts = {}
    for date, norm_desc, amount, cnt in rows:
        key = (date, norm_desc or "", Decimal(str(amount)))
        counts[key] = cnt

    return counts


def find_transactions_to_delete(conn, key: tuple[str, str, Decimal], excess: int) -> list[str]:
    date, norm_desc, amount = key
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id FROM transactions
            WHERE date = %s AND normalized_description = %s AND amount = %s
            ORDER BY created_at DESC
            LIMIT %s
        """,
            (date, norm_desc, amount, excess),
        )
        rows = cur.fetchall()
    return [str(row[0]) for row in rows]


def delete_transactions(conn, transaction_ids: list[str], dry_run: bool):
    if not transaction_ids:
        return
    if dry_run:
        print(f"  [DRY RUN] Would delete {len(transaction_ids)} transactions")
        return

    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM transactions WHERE id = ANY(%s)",
            (transaction_ids,),
        )
    conn.commit()
    print(f"  Deleted {len(transaction_ids)} transactions")


def main():
    parser = argparse.ArgumentParser(description="Clean up duplicate transactions")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--csv-dir", default="data/statements", help="Directory containing CSV files")
    parser.add_argument("--exclude", nargs="*", default=[], help="Patterns to exclude from CSV files (e.g., merged all)")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    database_url = database_url.replace("postgresql+psycopg://", "postgresql://")

    csv_dir = Path(args.csv_dir)
    if not csv_dir.exists():
        print(f"ERROR: CSV directory not found: {csv_dir}")
        sys.exit(1)

    print("=" * 60)
    print("DUPLICATE TRANSACTION CLEANUP")
    print("=" * 60)
    if args.dry_run:
        print("MODE: DRY RUN (no changes will be made)")
    print()

    print("Step 1: Parsing CSV files...")
    if args.exclude:
        print(f"  Excluding patterns: {args.exclude}")
    csv_counts = get_csv_counts(csv_dir, args.exclude)
    print(f"  Found {len(csv_counts)} unique transaction signatures in CSVs")
    total_csv_transactions = sum(csv_counts.values())
    print(f"  Total transactions in CSVs: {total_csv_transactions}")
    print()

    print("Step 2: Connecting to database...")
    conn = psycopg.connect(database_url)
    print("  Connected successfully")
    print()

    print("Step 3: Getting database counts...")
    db_counts = get_db_counts(conn)
    print(f"  Found {len(db_counts)} unique transaction signatures in DB")
    total_db_transactions = sum(db_counts.values())
    print(f"  Total transactions in DB: {total_db_transactions}")
    print()

    print("Step 4: Finding excess transactions...")
    excess_keys = []
    total_excess = 0
    for key, db_count in db_counts.items():
        csv_count = csv_counts.get(key, 0)
        excess = db_count - csv_count
        if excess > 0:
            excess_keys.append((key, excess, db_count, csv_count))
            total_excess += excess

    print(f"  Found {len(excess_keys)} transaction groups with excess")
    print(f"  Total excess transactions to delete: {total_excess}")
    print()

    if not excess_keys:
        print("No duplicates found. Database is clean.")
        conn.close()
        return

    print("Step 5: Deleting excess transactions...")
    for key, excess, db_count, csv_count in excess_keys:
        date, norm_desc, amount = key
        print(f"  {date} | {norm_desc[:40]:40} | {amount:>10} | DB:{db_count} CSV:{csv_count} Excess:{excess}")
        ids_to_delete = find_transactions_to_delete(conn, key, excess)
        delete_transactions(conn, ids_to_delete, args.dry_run)

    conn.close()

    print()
    print("=" * 60)
    if args.dry_run:
        print(f"DRY RUN COMPLETE: Would delete {total_excess} transactions")
    else:
        print(f"CLEANUP COMPLETE: Deleted {total_excess} transactions")
    print("=" * 60)


if __name__ == "__main__":
    main()
