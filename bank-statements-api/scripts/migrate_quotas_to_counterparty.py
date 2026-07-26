#!/usr/bin/env python3
"""
Migrate per-apartment income subcategories into counterparties.

Before: income category "Quotas" has one subcategory per apartment (1D, 1E, ...);
rules and transactions are categorised into those subcategories.

After: "Quotas" becomes a leaf income category; each apartment becomes a
counterparty Account. Rules and transactions are repointed to
category="Quotas" + counterparty=<apartment account>, and the now-empty
apartment subcategories are deleted.

Idempotent: once the subcategories are gone there is nothing left to migrate.

Usage:
    python scripts/migrate_quotas_to_counterparty.py <user_email> [--parent Quotas] [--dry-run]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.domain.models.categorization  # noqa: F401 -- register ORM mappers
import app.domain.models.enhancement_rule  # noqa: F401
import app.domain.models.filter_preset  # noqa: F401
import app.domain.models.refresh_token  # noqa: F401
import app.domain.models.saved_filter  # noqa: F401
import app.domain.models.user  # noqa: F401
from app.core.database import SessionLocal
from app.domain.models.account import Account
from app.domain.models.category import Category, CategoryKind
from app.domain.models.enhancement_rule import EnhancementRule
from app.domain.models.transaction import CounterpartyStatus, Transaction
from app.domain.models.user import User


def find_or_create_account(session, user_id, name, currency, dry_run):
    account = session.query(Account).filter(Account.user_id == user_id, Account.name == name).first()
    if account:
        print(f"  account exists: {name!r} ({account.id})")
        return account, False
    account = Account(user_id=user_id, name=name, currency=currency)
    if not dry_run:
        session.add(account)
        session.flush()
    print(f"  create account: {name!r}")
    return account, True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("email")
    parser.add_argument("--parent", default="Quotas", help="Name of the parent income category (default: Quotas)")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == args.email).first()
        if not user:
            print(f"No user with email {args.email!r}.")
            sys.exit(1)

        parent = (
            session.query(Category)
            .filter(
                Category.user_id == user.id,
                Category.name == args.parent,
                Category.parent_id.is_(None),
            )
            .first()
        )
        if not parent:
            print(f"No root category named {args.parent!r} for {user.email}.")
            sys.exit(1)
        if parent.kind != CategoryKind.INCOME:
            print(f"WARNING: category {args.parent!r} has kind={parent.kind}, expected income.")

        apartments = session.query(Category).filter(Category.parent_id == parent.id).all()
        if not apartments:
            print(f"No subcategories under {args.parent!r}. Nothing to migrate.")
            return

        currency = parent.user.accounts[0].currency if parent.user.accounts else "EUR"
        print(f"User: {user.email}")
        print(f"Parent category: {args.parent!r} ({parent.id})")
        print(f"Apartments ({len(apartments)}): {', '.join(c.name for c in apartments)}")
        print(f"Counterparty account currency: {currency}\n")

        accounts_created = 0
        rules_repointed = 0
        txns_repointed = 0

        for apt in apartments:
            print(f"Apartment {apt.name!r} ({apt.id}):")
            account, created = find_or_create_account(session, user.id, apt.name, currency, args.dry_run)
            if created:
                accounts_created += 1

            rules = (
                session.query(EnhancementRule)
                .filter(EnhancementRule.user_id == user.id, EnhancementRule.category_id == apt.id)
                .all()
            )
            for rule in rules:
                rule.category_id = parent.id
                rule.counterparty_account_id = account.id
                rules_repointed += 1
            if rules:
                print(f"  repoint {len(rules)} rule(s) -> category={args.parent!r}, counterparty={apt.name!r}")

            ai_rules = (
                session.query(EnhancementRule)
                .filter(EnhancementRule.user_id == user.id, EnhancementRule.ai_suggested_category_id == apt.id)
                .all()
            )
            for rule in ai_rules:
                rule.ai_suggested_category_id = None
            if ai_rules:
                print(f"  clear ai_suggested_category on {len(ai_rules)} rule(s)")

            txns = session.query(Transaction).filter(Transaction.user_id == user.id, Transaction.category_id == apt.id).all()
            for txn in txns:
                txn.category_id = parent.id
                txn.counterparty_account_id = account.id
                txn.counterparty_status = CounterpartyStatus.RULE_BASED
                txns_repointed += 1
            if txns:
                print(f"  repoint {len(txns)} transaction(s) -> category={args.parent!r}, counterparty={apt.name!r}")

            if not args.dry_run:
                session.flush()
            session.delete(apt)
            print(f"  delete subcategory {apt.name!r}\n")

        print("Summary:")
        print(f"  accounts created:   {accounts_created}")
        print(f"  rules repointed:    {rules_repointed}")
        print(f"  txns repointed:     {txns_repointed}")
        print(f"  subcats deleted:    {len(apartments)}")

        if args.dry_run:
            session.rollback()
            print("\n(DRY RUN — no changes written.)")
        else:
            session.commit()
            print("\nDone.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
