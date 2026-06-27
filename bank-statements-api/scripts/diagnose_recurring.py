#!/usr/bin/env python3
"""
Diagnose why specific merchants are not being detected as recurring patterns.

For each merchant keyword, prints:
  - matching transactions
  - distinct normalized_descriptions (and their counts)
  - distinct categories (and their counts)
  - intervals between consecutive transactions
  - a verdict on why the recurring analyser would drop it

Usage:
    python scripts/diagnose_recurring.py <user_email> <keyword> [<keyword> ...]

Example:
    python scripts/diagnose_recurring.py pedro@example.com apple youtube google chatgpt openai medium tickt
"""

import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func

from app.core.database import SessionLocal
from app.domain.models import (  # noqa: F401 -- ensure all mappers are registered
    account,
    background_job,
    categorization,
    category,
    enhancement_rule,
    enhancement_rule_pattern,
    enhancement_rule_split_line,
    filter_preset,
    initial_balance,
    processing,
    refresh_token,
    saved_filter,
    statement,
    subscription,
    tag,
    transaction,
    uploaded_file,
    user,
)
from app.domain.models.category import Category
from app.domain.models.transaction import Transaction
from app.domain.models.user import User

MONTHLY_MIN_OCCURRENCES = 3
MONTHLY_INTERVAL_MIN = 25
MONTHLY_INTERVAL_MAX = 38
QUARTERLY_INTERVAL_MIN = 80
QUARTERLY_INTERVAL_MAX = 100
YEARLY_MIN_OCCURRENCES = 2
YEARLY_INTERVAL_MIN = 350
YEARLY_INTERVAL_MAX = 380


def classify_interval(days: int) -> str:
    if MONTHLY_INTERVAL_MIN <= days <= MONTHLY_INTERVAL_MAX:
        return "monthly"
    if QUARTERLY_INTERVAL_MIN <= days <= QUARTERLY_INTERVAL_MAX:
        return "quarterly"
    if YEARLY_INTERVAL_MIN <= days <= YEARLY_INTERVAL_MAX:
        return "yearly"
    return "off"


def diagnose(session, user_id, keyword: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"KEYWORD: {keyword!r}")
    print("=" * 78)

    rows = (
        session.query(
            Transaction.id,
            Transaction.date,
            Transaction.description,
            Transaction.normalized_description,
            Transaction.amount,
            Transaction.category_id,
            Category.name.label("category_name"),
        )
        .outerjoin(Category, Category.id == Transaction.category_id)
        .filter(Transaction.user_id == user_id)
        .filter(
            func.lower(Transaction.description).like(f"%{keyword.lower()}%")
            | func.lower(Transaction.normalized_description).like(f"%{keyword.lower()}%")
        )
        .order_by(Transaction.date)
        .all()
    )

    if not rows:
        print(f"  No transactions found matching {keyword!r}.")
        return

    print(f"  Total matches: {len(rows)}")

    norm_counts = Counter(r.normalized_description for r in rows)
    print(f"\n  Distinct normalized_description values ({len(norm_counts)}):")
    for nd, c in norm_counts.most_common():
        print(f"    [{c:3d}]  {nd!r}")

    cat_counts = Counter((r.category_name or "<uncategorised>") for r in rows)
    print(f"\n  Distinct categories ({len(cat_counts)}):")
    for cat, c in cat_counts.most_common():
        print(f"    [{c:3d}]  {cat}")

    pair_counts = Counter((r.normalized_description, r.category_name or "<uncategorised>") for r in rows)
    print("\n  (normalized_description, category) groups — the analyser's grouping key:")
    for (nd, cat), c in pair_counts.most_common():
        marker = "OK" if c >= MONTHLY_MIN_OCCURRENCES else "TOO FEW"
        print(f"    [{c:3d}]  {marker:7}  cat={cat!r}  nd={nd!r}")

    if len(rows) <= 60:
        print("\n  Transactions (date | amount | category | normalized_description):")
        for r in rows:
            print(
                f"    {r.date.isoformat()}  {float(r.amount):10.2f}  "
                f"{(r.category_name or '<uncat>')[:20]:20}  {r.normalized_description!r}"
            )

        if len(rows) >= 2:
            print("\n  Intervals between consecutive matches (ignoring grouping):")
            for prev, curr in zip(rows, rows[1:]):
                days = (curr.date - prev.date).days
                print(f"    {prev.date} -> {curr.date}  = {days:4d} days  [{classify_interval(days)}]")
    else:
        print(f"\n  ({len(rows)} matches — per-transaction listing skipped. Use a more specific keyword to see them.)")

    print("\n  VERDICT:")
    if len(rows) < MONTHLY_MIN_OCCURRENCES:
        print(
            f"    Only {len(rows)} match(es) total — below monthly min "
            f"({MONTHLY_MIN_OCCURRENCES}). May still be a yearly candidate if 2+ with ~365d gap."
        )
    biggest_group = pair_counts.most_common(1)[0]
    (nd, cat), biggest_count = biggest_group
    if biggest_count < MONTHLY_MIN_OCCURRENCES and len(rows) >= MONTHLY_MIN_OCCURRENCES:
        print(
            f"    Biggest (normalized_description, category) group has only {biggest_count} "
            f"transactions — below monthly threshold. The merchant is being SPLIT by "
            f"either normalisation or categorisation."
        )
    if len(norm_counts) > 1:
        print(
            f"    -> {len(norm_counts)} distinct normalized_descriptions: normalisation is "
            f"not collapsing this merchant to a single key."
        )
    if len(cat_counts) > 1:
        print(
            f"    -> {len(cat_counts)} distinct categories: categorisation is inconsistent "
            f"across occurrences, which splits the grouping key."
        )


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    user_email = sys.argv[1]
    keywords = sys.argv[2:]

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"No user found with email {user_email!r}.")
            sys.exit(1)
        print(f"User: {user.email} (id={user.id})")
        print(f"Today: {date.today().isoformat()}")
        for kw in keywords:
            diagnose(session, user.id, kw)
    finally:
        session.close()


if __name__ == "__main__":
    main()
