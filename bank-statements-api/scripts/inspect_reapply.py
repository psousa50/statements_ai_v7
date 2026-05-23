#!/usr/bin/env python3
"""
Inspect which transactions would be re-routed by reapply_rules.py, with full
category paths (Parent > Subcategory) and the rule that won.

Usage:
    python scripts/inspect_reapply.py <user_email> [--from "Storage"] [--to "Youtube Premium"]

Filters are matched against the LEAF category name (not the parent path).
Both filters are optional; omit to list every change.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.domain.models.categorization  # noqa: F401 -- register ORM mappers
import app.domain.models.description_group  # noqa: F401
import app.domain.models.enhancement_rule  # noqa: F401
import app.domain.models.filter_preset  # noqa: F401
import app.domain.models.refresh_token  # noqa: F401
import app.domain.models.saved_filter  # noqa: F401
import app.domain.models.user  # noqa: F401
from app.core.database import SessionLocal
from app.domain.models.category import Category
from app.domain.models.enhancement_rule import EnhancementRule
from app.domain.models.transaction import Transaction
from app.domain.models.user import User
from scripts.reapply_rules import (
    REAPPLICABLE_CATEGORIZATION_STATUSES,
    candidate_rules_for,
    index_rules_by_pattern,
)


def category_path(cat_id, cats_by_id):
    if cat_id is None:
        return "<none>"
    cat = cats_by_id.get(cat_id)
    if cat is None:
        return f"<unknown {cat_id}>"
    if cat.parent_id and cat.parent_id in cats_by_id:
        return f"{cats_by_id[cat.parent_id].name} > {cat.name}"
    return cat.name


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("email")
    parser.add_argument("--from", dest="from_name", default=None)
    parser.add_argument("--to", dest="to_name", default=None)
    args = parser.parse_args()

    session = SessionLocal()
    try:
        u = session.query(User).filter(User.email == args.email).first()
        if not u:
            print(f"No user with email {args.email!r}.")
            sys.exit(1)

        rules = session.query(EnhancementRule).filter(EnhancementRule.user_id == u.id).all()
        by_exact, prefixes, infixes = index_rules_by_pattern(rules)

        cats_by_id = {c.id: c for c in session.query(Category).filter(Category.user_id == u.id).all()}
        cat_name_lower_to_ids = {}
        for c in cats_by_id.values():
            cat_name_lower_to_ids.setdefault(c.name.lower(), set()).add(c.id)

        from_ids = cat_name_lower_to_ids.get(args.from_name.lower()) if args.from_name else None
        to_ids = cat_name_lower_to_ids.get(args.to_name.lower()) if args.to_name else None

        shown = 0
        for txn in session.query(Transaction).filter(Transaction.user_id == u.id).yield_per(500):
            candidates = candidate_rules_for(txn, by_exact, prefixes, infixes)
            chosen = next((r for r in candidates if r.matches_transaction(txn)), None)
            if chosen is None or chosen.category_id is None:
                continue
            if chosen.category_id == txn.category_id:
                continue
            if txn.categorization_status not in REAPPLICABLE_CATEGORIZATION_STATUSES:
                continue
            if from_ids and txn.category_id not in from_ids:
                continue
            if to_ids and chosen.category_id not in to_ids:
                continue

            shown += 1
            old_path = category_path(txn.category_id, cats_by_id)
            new_path = category_path(chosen.category_id, cats_by_id)
            constraint = []
            if chosen.min_amount is not None or chosen.max_amount is not None:
                constraint.append(f"amount=[{chosen.min_amount}, {chosen.max_amount}]")
            if chosen.start_date is not None or chosen.end_date is not None:
                constraint.append(f"date=[{chosen.start_date}, {chosen.end_date}]")
            constraint_str = " " + ", ".join(constraint) if constraint else ""

            print(
                f"{txn.date}  {float(txn.amount):>10.2f}  "
                f"{txn.description[:38]:38}  nd={txn.normalized_description!r}\n"
                f"            {old_path}  ->  {new_path}\n"
                f"            rule: {chosen.match_type.value} {chosen.normalized_description_pattern!r}{constraint_str}\n"
            )

        print(f"Total rows shown: {shown}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
