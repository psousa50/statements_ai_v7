#!/usr/bin/env python3
"""
Re-apply enhancement rules to all of a user's existing transactions.

Useful after:
- Fixing the multi-rule-per-description matching bug.
- Adding or editing a rule with amount/date constraints.
- Bulk-importing rules.

For each transaction whose categorisation_status is UNCATEGORIZED, RULE_BASED,
or FAILURE (never MANUAL), this script finds all candidate rules, sorts them
by specificity (amount-constrained > date-constrained > EXACT > PREFIX > INFIX),
and applies the first one that matches in full.

Usage:
    python scripts/reapply_rules.py <user_email> [--dry-run] [--limit N]
"""

import argparse
import sys
from collections import defaultdict
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
from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus, Transaction
from app.domain.models.user import User
from app.services.transaction_rule_enhancement import _rule_specificity_key

REAPPLICABLE_CATEGORIZATION_STATUSES = {
    CategorizationStatus.UNCATEGORIZED,
    CategorizationStatus.RULE_BASED,
    CategorizationStatus.FAILURE,
}
REAPPLICABLE_COUNTERPARTY_STATUSES = {
    CounterpartyStatus.UNPROCESSED,
    CounterpartyStatus.RULE_BASED,
    CounterpartyStatus.FAILURE,
}


def index_rules_by_pattern(rules):
    by_exact = defaultdict(list)
    prefixes = []
    infixes = []
    for rule in rules:
        if rule.match_type.value == "exact":
            by_exact[rule.normalized_description_pattern.lower()].append(rule)
        elif rule.match_type.value == "prefix":
            prefixes.append(rule)
        else:
            infixes.append(rule)
    return by_exact, prefixes, infixes


def candidate_rules_for(transaction, by_exact, prefixes, infixes):
    nd = (transaction.normalized_description or "").lower()
    if not nd:
        return []
    matches = list(by_exact.get(nd, []))
    matches.extend(r for r in prefixes if nd.startswith(r.normalized_description_pattern.lower()))
    matches.extend(r for r in infixes if r.normalized_description_pattern.lower() in nd)
    return sorted(matches, key=_rule_specificity_key)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("email")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    parser.add_argument("--limit", type=int, default=None, help="Stop after N transactions evaluated")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        u = session.query(User).filter(User.email == args.email).first()
        if not u:
            print(f"No user with email {args.email!r}.")
            sys.exit(1)

        rules = session.query(EnhancementRule).filter(EnhancementRule.user_id == u.id).all()
        print(f"User: {u.email}  rules: {len(rules)}")

        by_exact, prefixes, infixes = index_rules_by_pattern(rules)

        cats_by_id = {c.id: c for c in session.query(Category).filter(Category.user_id == u.id).all()}

        def category_path(cat_id):
            if cat_id is None:
                return "<none>"
            cat = cats_by_id.get(cat_id)
            if cat is None:
                return f"<unknown {cat_id}>"
            if cat.parent_id and cat.parent_id in cats_by_id:
                return f"{cats_by_id[cat.parent_id].name} > {cat.name}"
            return cat.name

        q = session.query(Transaction).filter(Transaction.user_id == u.id)
        if args.limit:
            q = q.limit(args.limit)

        evaluated = 0
        category_changes = 0
        counterparty_changes = 0
        skipped_manual = 0
        changes_by_pair = defaultdict(int)

        for txn in q.yield_per(500):
            evaluated += 1
            candidates = candidate_rules_for(txn, by_exact, prefixes, infixes)
            chosen = next((r for r in candidates if r.matches_transaction(txn)), None)
            if chosen is None:
                continue

            updated = False

            if chosen.category_id is not None and chosen.category_id != txn.category_id:
                if txn.categorization_status == CategorizationStatus.MANUAL:
                    skipped_manual += 1
                elif txn.categorization_status in REAPPLICABLE_CATEGORIZATION_STATUSES:
                    pair = (
                        category_path(txn.category_id),
                        category_path(chosen.category_id),
                    )
                    changes_by_pair[pair] += 1
                    txn.category_id = chosen.category_id
                    txn.categorization_status = CategorizationStatus.RULE_BASED
                    category_changes += 1
                    updated = True

            if (
                chosen.counterparty_account_id is not None
                and chosen.counterparty_account_id != txn.counterparty_account_id
                and txn.counterparty_status in REAPPLICABLE_COUNTERPARTY_STATUSES
            ):
                txn.counterparty_account_id = chosen.counterparty_account_id
                txn.counterparty_status = CounterpartyStatus.RULE_BASED
                counterparty_changes += 1
                updated = True

            if updated and not args.dry_run:
                session.add(txn)

        if not args.dry_run:
            session.commit()

        print(f"\nEvaluated: {evaluated}")
        print(f"Category changes: {category_changes}")
        print(f"Counterparty changes: {counterparty_changes}")
        print(f"Skipped (MANUAL): {skipped_manual}")
        print("\nTop category re-routings (from -> to: count):")
        for (frm, to), c in sorted(changes_by_pair.items(), key=lambda kv: -kv[1])[:20]:
            print(f"  [{c:5d}]  {frm!r}  ->  {to!r}")
        if args.dry_run:
            print("\n(DRY RUN — no changes written.)")
    finally:
        session.close()


if __name__ == "__main__":
    main()
