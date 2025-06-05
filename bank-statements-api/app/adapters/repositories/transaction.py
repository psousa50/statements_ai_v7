from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
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

        if filters:
            query = query.filter(and_(*filters))

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        transactions = query.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()

        return transactions, total

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

    def find_duplicates(self, transactions: List[TransactionDTO]) -> List[TransactionDTO]:
        """
        Find duplicate transactions based on date, description, amount, and source.
        """
        if not transactions:
            return []

        duplicates = []

        for transaction_dto in transactions:
            # Convert source_id to UUID only if it's not already a UUID
            if transaction_dto.source_id:
                if isinstance(transaction_dto.source_id, UUID):
                    source_uuid = transaction_dto.source_id
                else:
                    source_uuid = UUID(transaction_dto.source_id)
            else:
                source_uuid = None

            existing = (
                self.db_session.query(Transaction)
                .filter(
                    Transaction.date == transaction_dto.date,
                    Transaction.description == transaction_dto.description,
                    Transaction.amount == transaction_dto.amount,
                    Transaction.source_id == source_uuid,
                )
                .first()
            )

            if existing:
                duplicates.append(transaction_dto)

        return duplicates

    def save_batch(self, transactions: List[TransactionDTO]) -> Tuple[int, int]:
        """
        Save a batch of transactions to the database with deduplication.
        """
        # Find duplicates before saving
        duplicates = self.find_duplicates(transactions)
        duplicates_count = len(duplicates)

        # Create a set of duplicate transactions for efficient lookup
        duplicate_tuples = set()
        for dup in duplicates:
            date_val = dup.date
            if isinstance(date_val, str):
                date_val = datetime.strptime(date_val, "%Y-%m-%d").date()
            duplicate_tuples.add((date_val, dup.description, float(dup.amount), dup.source_id))

        saved_count = 0
        for transaction_dto in transactions:
            date_val = transaction_dto.date
            if isinstance(date_val, str):
                date_val = datetime.strptime(date_val, "%Y-%m-%d").date()

            # Check if this transaction is a duplicate
            transaction_tuple = (
                date_val,
                transaction_dto.description,
                float(transaction_dto.amount),
                transaction_dto.source_id,
            )
            if transaction_tuple in duplicate_tuples:
                continue  # Skip duplicate transactions

            transaction = Transaction(
                date=date_val,
                amount=transaction_dto.amount,
                description=transaction_dto.description,
                normalized_description=normalize_description(transaction_dto.description),
                uploaded_file_id=transaction_dto.uploaded_file_id,
            )

            if transaction_dto.source_id:
                transaction.source_id = transaction_dto.source_id

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
        return self.db_session.query(Transaction).filter(Transaction.uploaded_file_id == uploaded_file_id).order_by(Transaction.date.asc()).all()
