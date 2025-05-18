from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import Transaction


class TransactionRepository(ABC):
    """
    Port (interface) for transaction repository operations.
    Following Hexagonal Architecture pattern.
    """

    @abstractmethod
    def create(self, transaction: Transaction) -> Transaction:
        """Create a new transaction"""
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get a transaction by ID"""
        pass

    @abstractmethod
    def get_all(self) -> List[Transaction]:
        """Get all transactions"""
        pass

    @abstractmethod
    def update(self, transaction: Transaction) -> Transaction:
        """Update a transaction"""
        pass

    @abstractmethod
    def delete(self, transaction_id: UUID) -> bool:
        """Delete a transaction"""
        pass

    @abstractmethod
    def save_batch(self, transactions: List[TransactionDTO]) -> int:
        """
        Save a batch of transactions to the database.

        Args:
            transactions: List of TransactionDTO objects with date, amount, description

        Returns:
            Number of transactions saved
        """
        pass

    @abstractmethod
    def get_oldest_uncategorized(self, limit: int = 10) -> List[Transaction]:
        """
        Get the oldest uncategorized transactions
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of uncategorized transactions, ordered by date (oldest first)
        """
        pass
