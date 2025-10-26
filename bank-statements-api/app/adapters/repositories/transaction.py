from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import pandas as pd
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.common.text_normalization import normalize_description
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.ports.repositories.transaction import TransactionRepository


class SQLAlchemyTransactionRepository(TransactionRepository):
    """
    SQLAlchemy implementation of the TransactionRepository.
    Adapter in the Hexagonal Architecture pattern.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, transaction: Transaction) -> Transaction:
        self.db_session.add(transaction)
        self.db_session.commit()
        self.db_session.refresh(transaction)
        return transaction

    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        return self.db_session.query(Transaction).filter(Transaction.id == transaction_id).first()

    def get_all(self) -> List[Transaction]:
        return (
            self.db_session.query(Transaction)
            .order_by(
                Transaction.date.desc(),
                Transaction.sort_index.asc(),
            )
            .all()
        )

    def get_all_by_account_and_date_range(
        self,
        account_id: UUID,
        end_date: date,
        start_date: Optional[date] = None,
    ) -> List[Transaction]:
        """Get all transactions for an account within a date range"""
        query = self.db_session.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.date <= end_date,
        )

        if start_date:
            query = query.filter(Transaction.date >= start_date)

        # Order by date and sort_index for consistent ordering
        return query.order_by(
            Transaction.date.asc(),
            Transaction.sort_index.asc(),
        ).all()

    def get_paginated(
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
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        exclude_transfers: Optional[bool] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
    ) -> Tuple[List[Transaction], int]:
        """Get transactions with pagination and advanced filtering"""

        # Build the base query
        query = self.db_session.query(Transaction)

        # Apply filters
        filters = []

        # Multiple category filter
        if category_ids:
            filters.append(Transaction.category_id.in_(category_ids))

        # Status filter
        if status is not None:
            filters.append(Transaction.categorization_status == status)

        # Amount range filters
        if min_amount is not None:
            filters.append(Transaction.amount >= min_amount)
        if max_amount is not None:
            filters.append(Transaction.amount <= max_amount)

        # Description search filter (case-insensitive, search in both description and normalized_description)
        if description_search:
            search_term = f"%{description_search.lower()}%"
            filters.append(
                or_(
                    func.lower(Transaction.description).like(search_term),
                    func.lower(Transaction.normalized_description).like(search_term),
                )
            )

        # Account filter
        if account_id is not None:
            filters.append(Transaction.account_id == account_id)

        # Date range filters
        if start_date is not None:
            filters.append(Transaction.date >= start_date)
        if end_date is not None:
            filters.append(Transaction.date <= end_date)

        # Exclude transfers filter (default to True)
        if exclude_transfers is not False:
            filters.append(Transaction.counterparty_account_id.is_(None))

        # Exclude uncategorized filter
        if exclude_uncategorized is True:
            filters.append(Transaction.category_id.isnot(None))

        # Transaction type filter
        if transaction_type == "debit":
            filters.append(Transaction.amount < 0)
        elif transaction_type == "credit":
            filters.append(Transaction.amount > 0)
        # For 'all' or None, don't add any filter

        if filters:
            query = query.filter(and_(*filters))

        # Get total count
        total = query.count()

        # Apply sorting
        order_clause = self._get_order_clause(sort_field, sort_direction)
        query = query.order_by(*order_clause)

        # Apply pagination
        transactions = query.offset((page - 1) * page_size).limit(page_size).all()

        return transactions, total

    def delete_by_statement_id(self, statement_id: UUID) -> int:
        """Delete all transactions associated with a statement"""
        transactions_to_delete = self.db_session.query(Transaction).filter(Transaction.statement_id == statement_id).all()

        count = len(transactions_to_delete)

        for transaction in transactions_to_delete:
            self.db_session.delete(transaction)

        self.db_session.flush()
        return count

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
        exclude_transfers: Optional[bool] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
    ) -> Dict[Optional[UUID], Dict[str, Decimal]]:
        """Get category totals for chart data with the same filtering options as get_paginated"""

        # Build the base query with aggregation
        query = self.db_session.query(
            Transaction.category_id,
            func.sum(func.abs(Transaction.amount)).label("total_amount"),
            func.count(Transaction.id).label("transaction_count"),
        )

        # Apply the same filters as get_paginated
        filters = []

        # Multiple category filter
        if category_ids:
            filters.append(Transaction.category_id.in_(category_ids))

        # Status filter
        if status is not None:
            filters.append(Transaction.categorization_status == status)

        # Amount range filters
        if min_amount is not None:
            filters.append(Transaction.amount >= min_amount)
        if max_amount is not None:
            filters.append(Transaction.amount <= max_amount)

        # Description search filter (case-insensitive, search in both description and normalized_description)
        if description_search:
            search_term = f"%{description_search.lower()}%"
            filters.append(
                or_(
                    func.lower(Transaction.description).like(search_term),
                    func.lower(Transaction.normalized_description).like(search_term),
                )
            )

        # Account filter
        if account_id is not None:
            filters.append(Transaction.account_id == account_id)

        # Date range filters
        if start_date is not None:
            filters.append(Transaction.date >= start_date)
        if end_date is not None:
            filters.append(Transaction.date <= end_date)

        # Exclude transfers filter (default to True)
        if exclude_transfers is not False:
            filters.append(Transaction.counterparty_account_id.is_(None))

        # Exclude uncategorized filter
        if exclude_uncategorized is True:
            filters.append(Transaction.category_id.isnot(None))

        # Transaction type filter
        if transaction_type == "debit":
            filters.append(Transaction.amount < 0)
        elif transaction_type == "credit":
            filters.append(Transaction.amount > 0)
        # For 'all' or None, don't add any filter

        if filters:
            query = query.filter(and_(*filters))

        # Group by category_id and execute
        results = query.group_by(Transaction.category_id).all()

        # Convert to the expected format
        totals = {}
        for (
            category_id,
            total_amount,
            transaction_count,
        ) in results:
            totals[category_id] = {
                "total_amount": Decimal(str(total_amount)) if total_amount else Decimal("0"),
                "transaction_count": Decimal(str(transaction_count)),
            }

        return totals

    def update(self, transaction: Transaction) -> Transaction:
        self.db_session.commit()
        self.db_session.refresh(transaction)
        return transaction

    def delete(self, transaction_id: UUID) -> bool:
        transaction = self.get_by_id(transaction_id)
        if transaction:
            self.db_session.delete(transaction)
            self.db_session.commit()
            return True
        return False

    def find_matching_transactions(
        self,
        date: str,
        description: str,
        amount: float,
        account_id: Optional[UUID] = None,
    ) -> List[Transaction]:
        """
        Find all transactions that match the given criteria.
        """
        # Convert date string to date object
        date_val = datetime.strptime(date, "%Y-%m-%d").date()

        # Convert amount to Decimal
        amount_val = Decimal(str(amount))

        # Normalize the description for comparison
        normalized_desc = normalize_description(description)

        # Build query
        query = self.db_session.query(Transaction).filter(
            Transaction.date == date_val,
            Transaction.normalized_description == normalized_desc,
            Transaction.amount == amount_val,
        )

        # Add account filter if provided
        if account_id is not None:
            query = query.filter(Transaction.account_id == account_id)

        return query.all()

    def save_batch(self, transactions: List[TransactionDTO]) -> Tuple[int, int]:
        """
        Save a batch of transactions to the database with deduplication.
        """
        saved_count = 0
        duplicates_count = 0
        processed_tx_ids = set()  # Track transaction IDs we've already matched

        for transaction_dto in transactions:
            # Skip transactions with invalid dates
            if not isinstance(transaction_dto.date, str) and pd.isna(transaction_dto.date):
                continue

            # Convert account_id to UUID if provided
            account_uuid = None
            if transaction_dto.account_id:
                if isinstance(transaction_dto.account_id, UUID):
                    account_uuid = transaction_dto.account_id
                else:
                    account_uuid = UUID(transaction_dto.account_id)

            # Prepare date string
            date_str = (
                transaction_dto.date if isinstance(transaction_dto.date, str) else transaction_dto.date.strftime("%Y-%m-%d")
            )

            # Find matching transactions in database
            matching_transactions = self.find_matching_transactions(
                date=date_str,
                description=transaction_dto.description,
                amount=float(transaction_dto.amount),
                account_id=account_uuid,
            )

            # Check if any matching transaction hasn't been marked as duplicate yet
            found_unused_duplicate = False
            for match in matching_transactions:
                if match.id not in processed_tx_ids:
                    processed_tx_ids.add(match.id)
                    found_unused_duplicate = True
                    duplicates_count += 1
                    break

            # If no unused duplicate found, save as new transaction
            if not found_unused_duplicate:
                date_val = transaction_dto.date
                if isinstance(date_val, str):
                    date_val = datetime.strptime(date_val, "%Y-%m-%d").date()

                # Convert account_type string to enum
                account_type_enum = SourceType.UPLOAD
                if transaction_dto.source_type == "manual":
                    account_type_enum = SourceType.MANUAL

                transaction = Transaction(
                    date=date_val,
                    amount=transaction_dto.amount,
                    description=transaction_dto.description,
                    normalized_description=normalize_description(transaction_dto.description),
                    statement_id=UUID(transaction_dto.statement_id) if transaction_dto.statement_id else None,
                    row_index=transaction_dto.row_index,
                    sort_index=transaction_dto.sort_index or 0,
                    source_type=account_type_enum,
                    manual_position_after=transaction_dto.manual_position_after,
                )

                if account_uuid:
                    transaction.account_id = account_uuid

                self.db_session.add(transaction)
                saved_count += 1

        self.db_session.commit()
        return saved_count, duplicates_count

    def get_oldest_uncategorized(self, limit: int = 10) -> List[Transaction]:
        return (
            self.db_session.query(Transaction)
            .filter(Transaction.categorization_status == CategorizationStatus.UNCATEGORIZED)
            .order_by(
                Transaction.date.asc(),
                Transaction.sort_index.asc(),
            )
            .limit(limit)
            .all()
        )

    def get_by_statement_id(self, statement_id: UUID) -> List[Transaction]:
        return (
            self.db_session.query(Transaction)
            .filter(Transaction.statement_id == statement_id)
            .order_by(
                Transaction.date.asc(),
                Transaction.sort_index.asc(),
            )
            .all()
        )

    def bulk_update_category_by_normalized_description(
        self,
        normalized_description: str,
        category_id: Optional[UUID],
    ) -> int:
        """
        Update the category for all transactions with the given normalized description.
        """
        query = self.db_session.query(Transaction).filter(Transaction.normalized_description == normalized_description)

        # Update the category_id and categorization_status for all matching transactions
        update_values = {
            "category_id": category_id,
            "categorization_status": (CategorizationStatus.CATEGORIZED if category_id else CategorizationStatus.UNCATEGORIZED),
        }

        # Execute bulk update
        updated_count = query.update(update_values)
        self.db_session.commit()

        return updated_count

    def get_max_sort_index_for_date(self, account_id: UUID, date: date) -> int:
        """
        Get the maximum sort_index for transactions on a given date and account.
        """
        result = (
            self.db_session.query(func.max(Transaction.sort_index))
            .filter(
                Transaction.account_id == account_id,
                Transaction.date == date,
            )
            .scalar()
        )
        return result or 0

    def create_transaction(
        self,
        transaction_data,
        after_transaction_id: Optional[UUID] = None,
    ) -> Transaction:
        """
        Create a transaction with proper sort_index assignment.
        """
        # Get next sort_index for the date
        max_sort = self.get_max_sort_index_for_date(
            transaction_data.account_id,
            transaction_data.date,
        )

        if after_transaction_id:
            after_transaction = self.get_by_id(after_transaction_id)
            if after_transaction:
                sort_index = after_transaction.sort_index + 10  # Gap strategy
            else:
                sort_index = max_sort + 10
        else:
            sort_index = max_sort + 10

        transaction = Transaction(
            date=transaction_data.date,
            amount=transaction_data.amount,
            description=transaction_data.description,
            normalized_description=normalize_description(transaction_data.description),
            account_id=transaction_data.account_id,
            sort_index=sort_index,
            source_type=SourceType.MANUAL,
            manual_position_after=after_transaction_id,
        )

        self.db_session.add(transaction)
        self.db_session.commit()
        self.db_session.refresh(transaction)
        return transaction

    def _get_order_clause(
        self,
        sort_field: Optional[str],
        sort_direction: Optional[str],
    ):
        """Build the ORDER BY clause based on sort parameters."""
        # Default sorting
        if not sort_field:
            return [
                Transaction.date.desc(),
                Transaction.sort_index.asc(),
            ]

        # Validate sort direction
        direction = sort_direction.lower() if sort_direction else "desc"
        if direction not in ["asc", "desc"]:
            direction = "desc"

        # Map sort fields to database columns
        if sort_field == "date":
            column = Transaction.date
        elif sort_field == "amount":
            column = Transaction.amount
        elif sort_field == "description":
            column = Transaction.description
        elif sort_field == "normalized_description":
            column = Transaction.normalized_description
        elif sort_field == "created_at":
            column = Transaction.created_at
        else:
            # Default to date for unknown fields
            column = Transaction.date

        # Apply direction - use same direction for both primary and secondary sort
        if direction == "asc":
            return [
                column.asc(),
                Transaction.sort_index.asc(),
            ]
        else:
            return [
                column.desc(),
                Transaction.sort_index.desc(),
            ]

    def count_matching_rule(self, rule, uncategorized_only: bool = False) -> int:
        """Count transactions that would match the given enhancement rule"""
        from app.domain.models.enhancement_rule import MatchType

        query = self.db_session.query(func.count(Transaction.id))

        # Match description pattern based on rule type
        if rule.match_type == MatchType.EXACT:
            query = query.filter(Transaction.normalized_description == rule.normalized_description_pattern)
        elif rule.match_type == MatchType.PREFIX:
            query = query.filter(Transaction.normalized_description.like(f"{rule.normalized_description_pattern}%"))
        elif rule.match_type == MatchType.INFIX:
            query = query.filter(Transaction.normalized_description.like(f"%{rule.normalized_description_pattern}%"))

        # Apply amount constraints if specified
        if rule.min_amount is not None:
            query = query.filter(Transaction.amount >= rule.min_amount)
        if rule.max_amount is not None:
            query = query.filter(Transaction.amount <= rule.max_amount)

        # Apply date constraints if specified
        if rule.start_date is not None:
            query = query.filter(Transaction.date >= rule.start_date)
        if rule.end_date is not None:
            query = query.filter(Transaction.date <= rule.end_date)

        if uncategorized_only:
            query = query.filter(Transaction.category_id.is_(None))

        result = query.scalar()
        return int(result) if result is not None else 0

    def find_transactions_matching_rule(
        self,
        rule,
        page: int = 1,
        page_size: int = 1000,
    ) -> List[Transaction]:
        """Find transactions that match the given enhancement rule with pagination"""
        from app.domain.models.enhancement_rule import MatchType

        query = self.db_session.query(Transaction)

        # Match description pattern based on rule type (same logic as count_matching_rule)
        if rule.match_type == MatchType.EXACT:
            query = query.filter(Transaction.normalized_description == rule.normalized_description_pattern)
        elif rule.match_type == MatchType.PREFIX:
            query = query.filter(Transaction.normalized_description.like(f"{rule.normalized_description_pattern}%"))
        elif rule.match_type == MatchType.INFIX:
            query = query.filter(Transaction.normalized_description.like(f"%{rule.normalized_description_pattern}%"))

        # Apply amount constraints if specified
        if rule.min_amount is not None:
            query = query.filter(Transaction.amount >= rule.min_amount)
        if rule.max_amount is not None:
            query = query.filter(Transaction.amount <= rule.max_amount)

        # Apply date constraints if specified
        if rule.start_date is not None:
            query = query.filter(Transaction.date >= rule.start_date)
        if rule.end_date is not None:
            query = query.filter(Transaction.date <= rule.end_date)

        # Add pagination
        offset = (page - 1) * page_size
        query = query.order_by(Transaction.date.desc(), Transaction.id.asc())
        query = query.offset(offset).limit(page_size)

        return query.all()

    def get_transactions_matching_rule_paginated(
        self,
        rule,
        page: int = 1,
        page_size: int = 20,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
    ) -> Tuple[List[Transaction], int]:
        """Get transactions that match the given enhancement rule with pagination and sorting"""
        from app.domain.models.enhancement_rule import MatchType

        query = self.db_session.query(Transaction)

        # Match description pattern based on rule type (same logic as count_matching_rule)
        if rule.match_type == MatchType.EXACT:
            query = query.filter(Transaction.normalized_description == rule.normalized_description_pattern)
        elif rule.match_type == MatchType.PREFIX:
            query = query.filter(Transaction.normalized_description.like(f"{rule.normalized_description_pattern}%"))
        elif rule.match_type == MatchType.INFIX:
            query = query.filter(Transaction.normalized_description.like(f"%{rule.normalized_description_pattern}%"))

        # Apply amount constraints if specified
        if rule.min_amount is not None:
            query = query.filter(Transaction.amount >= rule.min_amount)
        if rule.max_amount is not None:
            query = query.filter(Transaction.amount <= rule.max_amount)

        # Apply date constraints if specified
        if rule.start_date is not None:
            query = query.filter(Transaction.date >= rule.start_date)
        if rule.end_date is not None:
            query = query.filter(Transaction.date <= rule.end_date)

        # Get total count
        total = query.count()

        # Apply sorting
        order_clause = self._get_order_clause(sort_field, sort_direction)
        query = query.order_by(*order_clause)

        # Apply pagination
        transactions = query.offset((page - 1) * page_size).limit(page_size).all()

        return transactions, total
