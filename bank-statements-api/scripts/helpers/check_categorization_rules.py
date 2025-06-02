#!/usr/bin/env python3
"""
Check Transaction Categorization Rules Status

This script checks the transaction_categorization table to see how many
categorization rules exist and their sources.
"""

from app.core.dependencies import get_dependencies


def main():
    print("📊 Checking transaction categorization rules...")

    with get_dependencies() as (external, internal):
        # Get statistics
        stats = internal.transaction_categorization_repository.get_statistics()

        print("\n📈 Rules Summary:")
        print(f"  Total rules: {stats['total_rules']}")
        print(f"  Manual rules: {stats['manual_rules']}")
        print(f"  AI rules: {stats['ai_rules']}")

        if stats["total_rules"] == 0:
            print("\n⚠️  No categorization rules found.")
            print("   Rules will be created when AI categorization succeeds.")
        else:
            print(f"\n✅ Found {stats['total_rules']} categorization rules.")


if __name__ == "__main__":
    main()
