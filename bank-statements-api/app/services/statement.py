from typing import List, Optional
from uuid import UUID

from app.domain.models.statement import Statement
from app.ports.repositories.statement import StatementRepository
from app.ports.repositories.transaction import TransactionRepository


class StatementService:
    def __init__(
        self,
        statement_repository: StatementRepository,
        transaction_repository: TransactionRepository,
    ):
        self.statement_repository = statement_repository
        self.transaction_repository = transaction_repository

    def get_all_statements(self, user_id: UUID) -> List[Statement]:
        return self.statement_repository.find_all(user_id)

    def get_statement_by_id(self, statement_id: UUID, user_id: UUID) -> Optional[Statement]:
        return self.statement_repository.find_by_id(statement_id, user_id)

    def delete_statement_with_transactions(self, statement_id: UUID, user_id: UUID) -> dict:
        statement = self.statement_repository.find_by_id(statement_id, user_id)
        if not statement:
            raise ValueError(f"Statement with ID {statement_id} not found")

        transaction_count = self.transaction_repository.delete_by_statement_id(statement_id)
        self.statement_repository.delete(statement_id, user_id)

        return {
            "message": f"Statement deleted successfully. {transaction_count} transactions were also deleted.",
            "transaction_count": transaction_count,
        }
