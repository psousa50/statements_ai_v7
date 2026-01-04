#!/usr/bin/env python3
import argparse
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd


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


def detect_format(df: pd.DataFrame) -> dict | None:
    cols = [c.lower().strip() for c in df.columns]
    if "date" in cols and "description" in cols and "amount" in cols:
        return {"date": "Date", "description": "Description", "amount": "Amount", "type": "simple"}
    if "data lanc." in cols or "data valor" in cols:
        date_col = "Data Lanc." if "Data Lanc." in df.columns else df.columns[0]
        desc_col = "Descrição" if "Descrição" in df.columns else df.columns[2]
        amount_col = "Valor" if "Valor" in df.columns else df.columns[3]
        return {"date": date_col, "description": desc_col, "amount": amount_col, "type": "ab7_pt"}
    return None


def parse_csv(filepath: Path) -> tuple[list[dict], set[str]]:
    """Returns (transactions, dates_covered)"""
    try:
        df = pd.read_csv(filepath, dtype=str)
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return [], set()

    mapping = detect_format(df)
    if not mapping:
        print(f"  Unknown format: {filepath}")
        return [], set()

    transactions = []
    dates = set()
    for idx, row in df.iterrows():
        date = parse_date(row.get(mapping["date"]))
        desc = str(row.get(mapping["description"], "")).strip()
        amount = parse_amount(row.get(mapping["amount"]))

        if date and desc and amount is not None:
            transactions.append({
                "date": date,
                "description": desc,
                "amount": float(amount),
                "source_file": filepath.name,
                "source_row": idx,
            })
            dates.add(date)

    return transactions, dates


def main():
    parser = argparse.ArgumentParser(description="Merge AB7 CSV files with proper deduplication")
    parser.add_argument("--input-dir", default="data/statements/ab7", help="Directory containing AB7 CSV files")
    parser.add_argument("--output", default="data/statements/ab7/ab7_merged_new.csv", help="Output merged CSV file")
    parser.add_argument("--exclude", nargs="*", default=["merged", "all"], help="Patterns to exclude")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be merged without writing")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"ERROR: Directory not found: {input_dir}")
        return

    csv_files = list(input_dir.glob("*.csv"))
    for pattern in args.exclude:
        csv_files = [f for f in csv_files if pattern.lower() not in f.name.lower()]

    print("=" * 70)
    print("AB7 CSV MERGE")
    print("=" * 70)
    print()

    print(f"Found {len(csv_files)} CSV files to process:")
    for f in csv_files:
        print(f"  - {f.name}")
    print()

    # Parse all files
    file_data = []
    for filepath in sorted(csv_files):
        print(f"Parsing: {filepath.name}")
        transactions, dates = parse_csv(filepath)
        if transactions:
            print(f"  -> {len(transactions)} txs, {min(dates)} to {max(dates)}")
            file_data.append((filepath, transactions, dates))
        else:
            print(f"  -> No valid transactions")

    if not file_data:
        print("No transactions found!")
        return

    print()
    print("=" * 70)
    print("MERGING STRATEGY")
    print("=" * 70)
    print("For each date, use transactions from the file with the most txs for that day.")
    print("This ensures we don't double-count overlapping periods.")
    print()

    # For each date, pick the file with the most transactions
    date_to_best_file = {}
    for filepath, transactions, dates in file_data:
        txs_by_date = defaultdict(list)
        for tx in transactions:
            txs_by_date[tx["date"]].append(tx)

        for date, txs in txs_by_date.items():
            if date not in date_to_best_file or len(txs) > len(date_to_best_file[date][1]):
                date_to_best_file[date] = (filepath.name, txs)

    # Collect all merged transactions
    merged = []
    source_stats = defaultdict(int)
    for date in sorted(date_to_best_file.keys()):
        source_file, txs = date_to_best_file[date]
        for tx in txs:
            merged.append(tx)
        source_stats[source_file] += len(txs)

    print("Transactions per source file:")
    for source, count in sorted(source_stats.items()):
        print(f"  {source}: {count}")
    print()
    print(f"Total merged transactions: {len(merged)}")
    print(f"Date range: {min(date_to_best_file.keys())} to {max(date_to_best_file.keys())}")
    print()

    # Check for potential issues - dates where we had to choose
    overlapping_dates = 0
    for date in date_to_best_file.keys():
        files_with_date = [f.name for f, txs, dates in file_data if date in dates]
        if len(files_with_date) > 1:
            overlapping_dates += 1

    print(f"Overlapping dates (resolved by picking best file): {overlapping_dates}")
    print()

    if args.dry_run:
        print("[DRY RUN] Would write to:", args.output)
        return

    # Write output
    output_path = Path(args.output)
    df = pd.DataFrame(merged)
    df = df.sort_values(["date", "amount"])
    df = df[["date", "description", "amount"]]  # Keep only essential columns
    df.columns = ["Date", "Description", "Amount"]
    df.to_csv(output_path, index=False)

    print(f"Written to: {output_path}")
    print("Done!")


if __name__ == "__main__":
    main()
