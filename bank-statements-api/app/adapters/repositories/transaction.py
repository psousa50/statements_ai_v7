from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.common.text_normalization import normalize_description
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import CategorizationStatus, Transaction
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
        return self.db_session.query(Transaction).order_by(Transaction.date.desc()).all()

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        category_ids: Optional[List[UUID]] = None,
        status: Optional[CategorizationStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        description_search: Optional[str] = None,
        source_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
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

        # Source filter
        if source_id is not None:
            filters.append(Transaction.source_id == source_id)

        # Date range filters
        if start_date is not None:
            filters.append(Transaction.date >= start_date)
        if end_date is not None:
            filters.append(Transaction.date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        transactions = query.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()

        return transactions, total

    def get_category_totals(
        self,
        category_ids: Optional[List[UUID]] = None,
        status: Optional[CategorizationStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        description_search: Optional[str] = None,
        source_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
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

        # Source filter
        if source_id is not None:
            filters.append(Transaction.source_id == source_id)

        # Date range filters
        if start_date is not None:
            filters.append(Transaction.date >= start_date)
        if end_date is not None:
            filters.append(Transaction.date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # Group by category_id and execute
        results = query.group_by(Transaction.category_id).all()

        # Convert to the expected format
        totals = {}
        for category_id, total_amount, transaction_count in results:
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
        source_id: Optional[UUID] = None,
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

        # Add source filter if provided
        if source_id is not None:
            query = query.filter(Transaction.source_id == source_id)

        return query.all()

    def save_batch(self, transactions: List[TransactionDTO]) -> Tuple[int, int]:
        """
        Save a batch of transactions to the database with deduplication.
        """
        saved_count = 0
        duplicates_count = 0
        processed_tx_ids = set()  # Track transaction IDs we've already matched

        for transaction_dto in transactions:
            # Convert source_id to UUID if provided
            source_uuid = None
            if transaction_dto.source_id:
                if isinstance(transaction_dto.source_id, UUID):
                    source_uuid = transaction_dto.source_id
                else:
                    source_uuid = UUID(transaction_dto.source_id)

            # Find matching transactions in database
            matching_transactions = self.find_matching_transactions(
                date=(
                    transaction_dto.date if isinstance(transaction_dto.date, str) else transaction_dto.date.strftime("%Y-%m-%d")
                ),
                description=transaction_dto.description,
                amount=float(transaction_dto.amount),
                source_id=source_uuid,
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

                transaction = Transaction(
                    date=date_val,
                    amount=transaction_dto.amount,
                    description=transaction_dto.description,
                    normalized_description=normalize_description(transaction_dto.description),
                    uploaded_file_id=UUID(transaction_dto.uploaded_file_id),
                )

                if source_uuid:
                    transaction.source_id = source_uuid

                self.db_session.add(transaction)
                saved_count += 1

        self.db_session.commit()
        return saved_count, duplicates_count

    def get_oldest_uncategorized(self, limit: int = 10) -> List[Transaction]:
        return (
            self.db_session.query(Transaction)
            .filter(Transaction.categorization_status == CategorizationStatus.UNCATEGORIZED)
            .order_by(Transaction.date.asc())
            .limit(limit)
            .all()
        )

    def get_by_uploaded_file_id(self, uploaded_file_id: UUID) -> List[Transaction]:
        return (
            self.db_session.query(Transaction)
            .filter(Transaction.uploaded_file_id == uploaded_file_id)
            .order_by(Transaction.date.asc())
            .all()
        )

    def bulk_update_category_by_normalized_description(self, normalized_description: str, category_id: Optional[UUID]) -> int:
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
