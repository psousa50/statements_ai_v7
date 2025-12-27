from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.api.schemas import TransactionCreateRequest
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import CategorizationStatus, Transaction


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
    def create_transaction(
        self,
        transaction_data: TransactionCreateRequest,
        after_transaction_id: Optional[UUID] = None,
    ) -> Transaction:
        """Create a transaction with proper ordering"""
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: UUID, user_id: UUID) -> Optional[Transaction]:
        pass

    @abstractmethod
    def get_all(self, user_id: UUID) -> List[Transaction]:
        pass

    @abstractmethod
    def get_all_by_account_and_date_range(
        self,
        account_id: UUID,
        end_date: date,
        start_date: Optional[date] = None,
    ) -> List[Transaction]:
        """Get all transactions for an account within a date range"""
        pass

    @abstractmethod
    def get_paginated(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        category_ids: Optional[List[UUID]] = None,
        status: Optional[CategorizationStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        description_search: Optional[str] = None,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        exclude_transfers: Optional[bool] = None,
        transaction_type: Optional[str] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_ids: Optional[List[UUID]] = None,
    ) -> Tuple[List[Transaction], int, Decimal]:
        """
        Get paginated transactions with filters.

        Returns:
            Tuple of (transactions, total_count, total_amount)
            - transactions: List of transactions for the current page
            - total_count: Total number of matching transactions
            - total_amount: Sum of amounts for all matching transactions
        """
        pass

    @abstractmethod
    def get_category_totals(
        self,
        user_id: UUID,
        category_ids: Optional[List[UUID]] = None,
        status: Optional[CategorizationStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        description_search: Optional[str] = None,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_transfers: Optional[bool] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
    ) -> Dict[Optional[UUID], Dict[str, Decimal]]:
        pass

    @abstractmethod
    def update(self, transaction: Transaction) -> Transaction:
        """Update a transaction"""
        pass

    @abstractmethod
    def delete(self, transaction_id: UUID, user_id: UUID) -> bool:
        pass

    @abstractmethod
    def save_batch(self, transactions: List[TransactionDTO]) -> Tuple[int, int]:
        """
        Save a batch of transactions to the database with deduplication.

        Args:
            transactions: List of TransactionDTO objects with date, amount, description

        Returns:
            Tuple of (number of transactions saved, number of duplicates found)

        Deprecated: Use create_many instead. This method will be removed in future versions.
        """
        pass

    @abstractmethod
    def create_many(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Create multiple transactions in a single batch operation.
        This is a clean repository method that only handles persistence.

        Args:
            transactions: List of Transaction entities to persist

        Returns:
            List of persisted Transaction entities with IDs populated
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

    @abstractmethod
    def get_by_statement_id(self, statement_id: UUID) -> List[Transaction]:
        """
        Get all transactions associated with a statement

        Args:
            statement_id: UUID of the statement

        Returns:
            List of transactions from the statement
        """
        pass

    @abstractmethod
    def find_matching_transactions(
        self,
        date: str,
        description: str,
        amount: float,
        account_id: Optional[UUID] = None,
    ) -> List[Transaction]:
        """
        Find all transactions that match the given criteria.

        Args:
            date: Transaction date in YYYY-MM-DD format
            description: Transaction description
            amount: Transaction amount
            account_id: Optional account ID filter

        Returns:
            List of matching transactions from the database
        """
        pass

    @abstractmethod
    def bulk_update_category_by_normalized_description(
        self,
        user_id: UUID,
        normalized_description: str,
        category_id: Optional[UUID],
    ) -> int:
        pass

    @abstractmethod
    def count_by_normalized_description(
        self,
        user_id: UUID,
        normalized_description: str,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_transfers: Optional[bool] = None,
    ) -> int:
        pass

    @abstractmethod
    def count_by_category_id(
        self,
        user_id: UUID,
        category_id: UUID,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_transfers: Optional[bool] = None,
    ) -> int:
        pass

    @abstractmethod
    def bulk_update_by_category_id(
        self,
        user_id: UUID,
        from_category_id: UUID,
        to_category_id: Optional[UUID],
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_transfers: Optional[bool] = None,
    ) -> int:
        pass

    @abstractmethod
    def count_matching_rule(self, rule, uncategorized_only: bool = False) -> int:
        """
        Count transactions that would match the given enhancement rule

        Args:
            rule: EnhancementRule to match against
            uncategorized_only: If True, only count transactions without a category

        Returns:
            Number of transactions that match the rule
        """
        pass

    @abstractmethod
    def find_transactions_matching_rule(
        self,
        rule,
        page: int = 1,
        page_size: int = 1000,
    ) -> List[Transaction]:
        """
        Find transactions that match the given enhancement rule with pagination

        Args:
            rule: EnhancementRule to match against
            page: Page number (1-based)
            page_size: Number of transactions per page

        Returns:
            List of matching transactions for the specified page
        """
        pass

    @abstractmethod
    def get_transactions_matching_rule_paginated(
        self,
        user_id: UUID,
        rule,
        page: int = 1,
        page_size: int = 20,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        uncategorized_only: bool = False,
    ) -> Tuple[List[Transaction], int]:
        pass

    @abstractmethod
    def delete_by_statement_id(self, statement_id: UUID) -> int:
        """
        Delete all transactions associated with a statement

        Args:
            statement_id: UUID of the statement

        Returns:
            Number of transactions deleted
        """
        pass

    @abstractmethod
    def get_unique_normalised_descriptions(self, user_id: UUID, limit: int = 200) -> List[str]:
        pass
