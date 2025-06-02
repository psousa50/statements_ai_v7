from datetime import datetime
from typing import List, Optional
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

    def save_batch(self, transactions: List[TransactionDTO]) -> int:
        saved_count = 0
        for transaction_dto in transactions:
            date_val = transaction_dto.date
            if isinstance(date_val, str):
                date_val = datetime.strptime(date_val, "%Y-%m-%d").date()

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
        return saved_count

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
