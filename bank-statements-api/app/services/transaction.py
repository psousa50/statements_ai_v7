from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.api.schemas import TransactionCreateRequest, TransactionListResponse
from app.common.text_normalization import normalize_description
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository


class TransactionService:
    """
    Application service for transaction operations.
    Contains business logic and uses the repository port.
    """

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        initial_balance_repository: InitialBalanceRepository,
        enhancement_rule_repository: EnhancementRuleRepository,
    ):
        self.transaction_repository = transaction_repository
        self.initial_balance_repository = initial_balance_repository
        self.enhancement_rule_repository = enhancement_rule_repository

    def create_transaction(
        self,
        transaction_data: TransactionCreateRequest,
        after_transaction_id: Optional[UUID] = None,
    ) -> Transaction:
        """
        Create a transaction with proper ordering.

        Args:
            transaction_data: The transaction data to create
            after_transaction_id: Optional transaction ID to insert after for ordering

        Returns:
            The created transaction with proper sort_index
        """
        return self.transaction_repository.create_transaction(
            transaction_data=transaction_data,
            after_transaction_id=after_transaction_id,
        )

    def get_transaction(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get a transaction by ID"""
        return self.transaction_repository.get_by_id(transaction_id)

    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions"""
        return self.transaction_repository.get_all()

    def get_transactions_paginated(
        self,
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
        include_running_balance: bool = False,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
    ) -> TransactionListResponse:
        """Get transactions with pagination and advanced filtering"""
        (
            transactions,
            total,
        ) = self.transaction_repository.get_paginated(
            page=page,
            page_size=page_size,
            category_ids=category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

        # Calculate running balance if requested and account is specified
        if include_running_balance and account_id is not None:
            self._add_running_balance_to_transactions(transactions, account_id)

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return TransactionListResponse(
            transactions=transactions,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_transactions_matching_rule_paginated(
        self,
        enhancement_rule_id: UUID,
        page: int = 1,
        page_size: int = 20,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        include_running_balance: bool = False,
    ) -> TransactionListResponse:
        """Get transactions that match the given enhancement rule with pagination"""

        # Get the enhancement rule
        rule = self.enhancement_rule_repository.find_by_id(enhancement_rule_id)
        if not rule:
            raise ValueError(f"Enhancement rule with ID {enhancement_rule_id} not found")

        # Get transactions matching the rule with pagination
        (
            transactions,
            total,
        ) = self.transaction_repository.get_transactions_matching_rule_paginated(
            rule=rule,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

        # Calculate running balance if requested (not supported for rule filtering since account may vary)
        # Note: Running balance calculation is complex for rule-based filtering since rules can span multiple accounts
        if include_running_balance:
            # We could implement this if needed, but it's complex when transactions span multiple accounts
            pass

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        # Add rule information to the response (we'll need to update the schema for this)
        response = TransactionListResponse(
            transactions=transactions,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

        # Store rule information for the frontend to display
        response.enhancement_rule = rule

        return response

    def _add_running_balance_to_transactions(
        self,
        transactions: List[Transaction],
        account_id: UUID,
    ):
        """Add running balance to transactions for a specific account"""
        if not transactions:
            return

        # Get the latest date from the current page of transactions
        latest_date = max(t.date for t in transactions)

        # Get all transactions up to the latest date for accurate running balance
        all_transactions = self.transaction_repository.get_all_by_account_and_date_range(
            account_id=account_id, end_date=latest_date
        )

        # Get the earliest transaction date
        earliest_date = min(t.date for t in all_transactions)

        # Get the latest initial balance before the earliest transaction date
        latest_balance = self.initial_balance_repository.get_latest_by_account_id_and_date(
            account_id=account_id, before_date=earliest_date
        )

        # For the first transactions of an account, start from 0 if no initial balance exists
        starting_balance = Decimal("0.00")
        if latest_balance and latest_balance.balance_date <= earliest_date:
            starting_balance = latest_balance.balance_amount

        # Sort all transactions by date and then by created_at (for consistent ordering of same-date transactions)
        sorted_transactions = sorted(
            all_transactions,
            key=lambda x: (x.date, x.created_at),
        )

        # Calculate running balance for all transactions
        balances = {}  # Keep track of running balance for each transaction
        current_balance = starting_balance
        for transaction in sorted_transactions:
            current_balance += transaction.amount
            balances[transaction.id] = current_balance

        # Update running balance only for transactions in the current page
        for transaction in transactions:
            transaction.running_balance = balances.get(transaction.id)

        # Note: We don't re-sort here to preserve the user's sorting preferences
        # The transactions are already sorted according to the user's sort_field and sort_direction

    def get_category_totals(
        self,
        category_ids: Optional[List[UUID]] = None,
        status: Optional[CategorizationStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        description_search: Optional[str] = None,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[Optional[UUID], Dict[str, Decimal]]:
        """Get category totals for chart data with the same filtering options as get_transactions_paginated"""
        return self.transaction_repository.get_category_totals(
            category_ids=category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
        )

    def update_transaction(
        self,
        transaction_id: UUID,
        transaction_date: date,
        description: str,
        amount: Decimal,
        account_id: UUID,
        category_id: Optional[UUID] = None,
    ) -> Optional[Transaction]:
        """Update a transaction"""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if transaction:
            transaction.date = transaction_date
            transaction.description = description
            transaction.normalized_description = normalize_description(description)
            transaction.amount = amount

            # Update category and categorization status
            transaction.category_id = category_id
            transaction.categorization_status = (
                CategorizationStatus.CATEGORIZED if category_id else CategorizationStatus.UNCATEGORIZED
            )

            # Update account
            transaction.account_id = account_id  # type: ignore

            return self.transaction_repository.update(transaction)
        return None

    def delete_transaction(self, transaction_id: UUID) -> bool:
        """Delete a transaction"""
        return self.transaction_repository.delete(transaction_id)

    def categorize_transaction(
        self,
        transaction_id: UUID,
        category_id: Optional[UUID],
    ) -> Optional[Transaction]:
        """Categorize a transaction"""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            return None

        transaction.category_id = category_id
        transaction.categorization_status = (
            CategorizationStatus.CATEGORIZED if category_id else CategorizationStatus.UNCATEGORIZED
        )

        return self.transaction_repository.update(transaction)

    def mark_categorization_failure(self, transaction_id: UUID) -> Optional[Transaction]:
        """Mark a transaction as having failed categorization"""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            return None

        transaction.categorization_status = CategorizationStatus.FAILURE

        return self.transaction_repository.update(transaction)

    def bulk_update_category_by_normalized_description(
        self,
        normalized_description: str,
        category_id: Optional[UUID],
    ) -> int:
        """Update the category for all transactions with the given normalized description"""
        return self.transaction_repository.bulk_update_category_by_normalized_description(normalized_description, category_id)
