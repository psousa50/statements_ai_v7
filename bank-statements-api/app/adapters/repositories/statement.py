from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.domain.models.statement import Statement
from app.domain.models.transaction import Transaction
from app.domain.models.account import Account
from app.ports.repositories.statement import StatementRepository


class SqlAlchemyStatementRepository(StatementRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self,
        account_id: UUID,
        filename: str,
        file_type: str,
        content: bytes,
    ) -> Statement:
        statement = Statement(
            account_id=account_id,
            filename=filename,
            file_type=file_type,
            content=content,
        )
        self.session.add(statement)
        self.session.flush()  # Flush to get the ID without committing
        return statement

    def find_by_id(self, statement_id: UUID) -> Optional[Statement]:
        return self.session.query(Statement).filter(Statement.id == statement_id).first()

    def find_by_account_id(self, account_id: UUID) -> list[Statement]:
        return self.session.query(Statement).filter(Statement.account_id == account_id).all()

    def find_all(self) -> list[Statement]:
        return self.session.query(Statement).options(joinedload(Statement.account)).order_by(Statement.created_at.desc()).all()

    def delete(self, statement_id: UUID) -> None:
        statement = self.session.query(Statement).filter(Statement.id == statement_id).first()
        if statement:
            self.session.delete(statement)
            self.session.flush()

    def update_transaction_statistics(self, statement_id: UUID) -> None:
        """Update statement with transaction count and date range"""
        # Get transaction statistics for this statement
        stats = (
            self.session.query(
                func.count(Transaction.id).label("transaction_count"),
                func.min(Transaction.date).label("date_from"),
                func.max(Transaction.date).label("date_to"),
            )
            .filter(Transaction.statement_id == statement_id)
            .first()
        )

        if stats and stats.transaction_count > 0:
            # Update the statement with the calculated statistics
            self.session.query(Statement).filter(Statement.id == statement_id).update(
                {"transaction_count": stats.transaction_count, "date_from": stats.date_from, "date_to": stats.date_to}
            )
            self.session.flush()
