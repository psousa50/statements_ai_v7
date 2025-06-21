from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.statement import Statement
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
