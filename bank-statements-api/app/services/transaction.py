from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.domain.models.transaction import Transaction
from app.ports.repositories.transaction import TransactionRepository


class TransactionService:
    """
    Application service for transaction operations.
    Contains business logic and uses the repository port.
    """
    
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository
    
    def create_transaction(self, transaction_date: date, description: str, amount: Decimal) -> Transaction:
        """Create a new transaction"""
        transaction = Transaction(
            date=transaction_date,
            description=description,
            amount=amount
        )
        return self.transaction_repository.create(transaction)
    
    def get_transaction(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get a transaction by ID"""
        return self.transaction_repository.get_by_id(transaction_id)
    
    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions"""
        return self.transaction_repository.get_all()
    
    def update_transaction(self, transaction_id: UUID, transaction_date: date, description: str, amount: Decimal) -> Optional[Transaction]:
        """Update a transaction"""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if transaction:
            transaction.date = transaction_date
            transaction.description = description
            transaction.amount = amount
            return self.transaction_repository.update(transaction)
        return None
    
    def delete_transaction(self, transaction_id: UUID) -> bool:
        """Delete a transaction"""
        return self.transaction_repository.delete(transaction_id)
