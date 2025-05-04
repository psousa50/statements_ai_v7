from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.transaction import Transaction
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
        print(f"Deleting transaction with ID: {transaction_id}")
        transaction = self.get_by_id(transaction_id)
        print(f"Transaction found: {transaction}")
        if transaction:
            print(f"Deleting transaction: {transaction}")
            self.db_session.delete(transaction)
            print(f"Committing the transaction deletion for ID: {transaction_id}")
            self.db_session.commit()
            print(f"Transaction with ID: {transaction_id} deleted successfully.")
            return True
        return False
