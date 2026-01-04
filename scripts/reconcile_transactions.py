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
    text = re.sub(r"\b(ref|reference|#|id|date)\b[:\s]*[\w\d\-\/\.]+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", "", text)
    text = re.sub(r"\bon\s+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", "", text)
    text = re.sub(r"[^a-z\s]", "", text)
    for word in ["id", "ref", "on", "at", "to", "from", "the", "and", "for"]:
        text = re.sub(r"\b" + word + r"\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_amount(val) -> Decimal | None:
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return Decimal(str(round(val, 2)))
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
        return Decimal(cleaned).quantize(Decimal("0.01"))
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


def parse_csv_file(filepath: Path) -> tuple[list[tuple[str, str, Decimal, str]], set[str]]:
    """Returns (transactions, dates_covered)"""
    try:
        df = pd.read_csv(filepath, dtype=str)
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return [], set()

    mapping = detect_csv_format(df)
    if not mapping:
        print(f"  Unknown format: {filepath}")
        return [], set()

    transactions = []
    dates = set()
    for _, row in df.iterrows():
        date = parse_date(row.get(mapping["date"]))
        desc = str(row.get(mapping["description"], ""))
        amount = parse_amount(row.get(mapping["amount"]))

        if date and amount is not None:
            norm_desc = normalize_description(desc)
            transactions.append((date, norm_desc, amount, desc[:60]))
            dates.add(date)

    return transactions, dates


def get_csv_transactions(csv_dir: Path, exclude_patterns: list[str] = None) -> dict[str, list[tuple[str, str, Decimal, str]]]:
    """Returns transactions grouped by date, deduplicated across overlapping files"""
    csv_files = list(csv_dir.glob("**/*.csv"))
    csv_files = [f for f in csv_files if "tests" not in str(f)]

    if exclude_patterns:
        for pattern in exclude_patterns:
            csv_files = [f for f in csv_files if pattern.lower() not in f.name.lower()]

    print(f"Found {len(csv_files)} CSV files to process")

    # Parse all files
    file_data = []
    for filepath in csv_files:
        print(f"  Processing: {filepath.name}")
        transactions, dates = parse_csv_file(filepath)
        if transactions:
            print(f"    -> {len(transactions)} txs, {min(dates)} to {max(dates)}")
            file_data.append((filepath.name, transactions, dates))

    # Group by date, taking transactions from the file with most transactions for that date
    date_to_file = {}  # date -> (filename, transactions for that date)

    for filename, transactions, dates in file_data:
        date_txs = defaultdict(list)
        for tx in transactions:
            date_txs[tx[0]].append(tx)

        for date, txs in date_txs.items():
            if date not in date_to_file or len(txs) > len(date_to_file[date][1]):
                date_to_file[date] = (filename, txs)

    # Flatten back to date -> transactions
    result = {}
    for date, (filename, txs) in date_to_file.items():
        result[date] = txs

    return result


def get_db_transactions(conn) -> dict[str, list[tuple[str, str, Decimal, str]]]:
    """Returns transactions grouped by date"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT date::text, normalized_description, amount, LEFT(description, 60)
            FROM transactions
            ORDER BY date, normalized_description, amount
        """)
        rows = cur.fetchall()

    result = defaultdict(list)
    for date, norm_desc, amount, desc in rows:
        result[date].append((date, norm_desc or "", Decimal(str(amount)).quantize(Decimal("0.01")), desc or ""))

    return dict(result)


def compare_day(csv_txs: list, db_txs: list, ignore_description: bool = False) -> tuple[list, list, int]:
    """Compare transactions for a single day. Returns (missing_in_db, excess_in_db, matched)"""
    # Create multisets (count occurrences)
    csv_counts = defaultdict(int)
    csv_descs = {}
    for tx in csv_txs:
        if ignore_description:
            key = (tx[0], tx[2])  # date, amount only
        else:
            key = (tx[0], tx[1], tx[2])  # date, norm_desc, amount
        csv_counts[key] += 1
        csv_descs[key] = tx[3]

    db_counts = defaultdict(int)
    db_descs = {}
    for tx in db_txs:
        if ignore_description:
            key = (tx[0], tx[2])  # date, amount only
        else:
            key = (tx[0], tx[1], tx[2])
        db_counts[key] += 1
        db_descs[key] = tx[3]

    missing_in_db = []
    excess_in_db = []
    matched = 0

    all_keys = set(csv_counts.keys()) | set(db_counts.keys())
    for key in all_keys:
        csv_count = csv_counts.get(key, 0)
        db_count = db_counts.get(key, 0)
        desc = csv_descs.get(key) or db_descs.get(key, "")

        if csv_count > db_count:
            missing_in_db.append((key, csv_count - db_count, desc))
        elif db_count > csv_count:
            excess_in_db.append((key, db_count - csv_count, desc))

        matched += min(csv_count, db_count)

    return missing_in_db, excess_in_db, matched


def main():
    parser = argparse.ArgumentParser(description="Reconcile CSV transactions with database")
    parser.add_argument("--csv-dir", default="data/statements", help="Directory containing CSV files")
    parser.add_argument("--exclude", nargs="*", default=[], help="Patterns to exclude from CSV files")
    parser.add_argument("--show-all", action="store_true", help="Show all discrepancies (not just summary)")
    parser.add_argument("--ignore-description", action="store_true", help="Match by date+amount only (ignore description differences)")
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

    print("=" * 70)
    print("TRANSACTION RECONCILIATION")
    print("=" * 70)
    print()

    print("Step 1: Parsing CSV files (deduplicating overlapping days)...")
    if args.exclude:
        print(f"  Excluding patterns: {args.exclude}")
    csv_by_date = get_csv_transactions(csv_dir, args.exclude)
    total_csv = sum(len(txs) for txs in csv_by_date.values())
    print(f"\n  Total unique CSV transactions: {total_csv}")
    print(f"  Date range: {min(csv_by_date.keys())} to {max(csv_by_date.keys())}")
    print()

    print("Step 2: Loading database transactions...")
    conn = psycopg.connect(database_url)
    db_by_date = get_db_transactions(conn)
    total_db = sum(len(txs) for txs in db_by_date.values())
    print(f"  Total DB transactions: {total_db}")
    print(f"  Date range: {min(db_by_date.keys())} to {max(db_by_date.keys())}")
    print()

    print("Step 3: Comparing by date...")
    if args.ignore_description:
        print("  (Matching by date+amount only, ignoring description)")
    all_dates = set(csv_by_date.keys()) | set(db_by_date.keys())

    total_missing = 0
    total_excess = 0
    total_matched = 0
    days_with_issues = []

    for date in sorted(all_dates):
        csv_txs = csv_by_date.get(date, [])
        db_txs = db_by_date.get(date, [])

        missing, excess, matched = compare_day(csv_txs, db_txs, args.ignore_description)

        missing_count = sum(m[1] for m in missing)
        excess_count = sum(e[1] for e in excess)

        total_missing += missing_count
        total_excess += excess_count
        total_matched += matched

        if missing or excess:
            days_with_issues.append((date, len(csv_txs), len(db_txs), missing, excess))

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  CSV transactions:     {total_csv:>8}")
    print(f"  DB transactions:      {total_db:>8}")
    print(f"  Matched:              {total_matched:>8}")
    print(f"  Missing in DB:        {total_missing:>8}  (in CSV but not in DB)")
    print(f"  Excess in DB:         {total_excess:>8}  (in DB but not in CSV - duplicates)")
    print(f"  Days with issues:     {len(days_with_issues):>8}")
    print()

    if days_with_issues and args.show_all:
        print("=" * 70)
        print("DETAILED DISCREPANCIES")
        print("=" * 70)
        for date, csv_count, db_count, missing, excess in days_with_issues:
            print(f"\n{date} (CSV: {csv_count}, DB: {db_count})")
            for key, count, desc in missing:
                amount = key[-1]  # amount is always last element
                print(f"  MISSING x{count}: {amount:>10} | {desc[:50]}")
            for key, count, desc in excess:
                amount = key[-1]
                print(f"  EXCESS  x{count}: {amount:>10} | {desc[:50]}")
    elif days_with_issues:
        print("Use --show-all to see detailed discrepancies")

    conn.close()


if __name__ == "__main__":
    main()
