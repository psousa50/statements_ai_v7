#!/usr/bin/env python
"""
Example script demonstrating how to use the dependency injection pattern
for scripts or one-off tasks.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.dependencies import get_dependencies


def main():
    """Main function."""
    print("Starting example script...")
    
    # Use the context manager to get dependencies
    with get_dependencies() as (external, internal):
        # Use the dependencies
        print("Getting all transactions...")
        transactions = internal.transaction_service.get_all_transactions()
        print(f"Found {len(transactions)} transactions")
        
        # Example of using the transaction service
        for transaction in transactions:
            print(f"Transaction: {transaction.date} - {transaction.description} - ${transaction.amount}")
    
    # The database connection is automatically closed when the context manager exits
    print("Script completed successfully!")


if __name__ == "__main__":
    main()
