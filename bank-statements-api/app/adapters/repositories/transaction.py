from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from app.common.text_normalization import normalize_description
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.repositories.transaction import TransactionRepository
from sqlalchemy.orm import Session


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
        return (
            self.db_session.query(Transaction)
            .filter(Transaction.id == transaction_id)
            .first()
        )

    def get_all(self) -> List[Transaction]:
        return (
            self.db_session.query(Transaction).order_by(Transaction.date.desc()).all()
        )

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

    def find_duplicates(
        self, transactions: List[TransactionDTO]
    ) -> List[TransactionDTO]:
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
            duplicate_tuples.add(
                (date_val, dup.description, float(dup.amount), dup.source_id)
            )

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
                normalized_description=normalize_description(
                    transaction_dto.description
                ),
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
            .filter(
                Transaction.categorization_status == CategorizationStatus.UNCATEGORIZED
            )
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
