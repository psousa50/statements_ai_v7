from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.repositories.transaction import TransactionRepository


class TransactionService:
    """
    Application service for transaction operations.
    Contains business logic and uses the repository port.
    """

    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def create_transaction(
        self,
        transaction_date: date,
        description: str,
        amount: Decimal,
        category_id: Optional[UUID] = None,
        source_id: Optional[UUID] = None,
    ) -> Transaction:
        """Create a new transaction"""
        transaction = Transaction(
            date=transaction_date,
            description=description,
            amount=amount,
            category_id=category_id,
            source_id=source_id,
            categorization_status=(CategorizationStatus.CATEGORIZED if category_id else CategorizationStatus.UNCATEGORIZED),
        )
        return self.transaction_repository.create(transaction)

    def get_transaction(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get a transaction by ID"""
        return self.transaction_repository.get_by_id(transaction_id)

    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions"""
        return self.transaction_repository.get_all()

    def update_transaction(
        self,
        transaction_id: UUID,
        transaction_date: date,
        description: str,
        amount: Decimal,
        category_id: Optional[UUID] = None,
        source_id: Optional[UUID] = None,
    ) -> Optional[Transaction]:
        """Update a transaction"""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if transaction:
            transaction.date = transaction_date
            transaction.description = description
            transaction.amount = amount

            # Update category and categorization status
            transaction.category_id = category_id
            transaction.categorization_status = CategorizationStatus.CATEGORIZED if category_id else CategorizationStatus.UNCATEGORIZED
            
            # Update source
            transaction.source_id = source_id

            return self.transaction_repository.update(transaction)
        return None

    def delete_transaction(self, transaction_id: UUID) -> bool:
        """Delete a transaction"""
        return self.transaction_repository.delete(transaction_id)

    def categorize_transaction(self, transaction_id: UUID, category_id: Optional[UUID]) -> Optional[Transaction]:
        """Categorize a transaction"""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            return None

        transaction.category_id = category_id
        transaction.categorization_status = CategorizationStatus.CATEGORIZED if category_id else CategorizationStatus.UNCATEGORIZED

        return self.transaction_repository.update(transaction)

    def mark_categorization_failure(self, transaction_id: UUID) -> Optional[Transaction]:
        """Mark a transaction as having failed categorization"""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            return None

        transaction.categorization_status = CategorizationStatus.FAILURE

        return self.transaction_repository.update(transaction)
