from typing import List, Optional
from uuid import UUID

from app.domain.models.statement import Statement
from app.ports.repositories.statement import StatementRepository
from app.ports.repositories.transaction import TransactionRepository


class StatementService:
    """
    Application service for statement operations.
    Provides business logic and transaction management for statement operations.
    """

    def __init__(
        self,
        statement_repository: StatementRepository,
        transaction_repository: TransactionRepository,
    ):
        self.statement_repository = statement_repository
        self.transaction_repository = transaction_repository

    def get_all_statements(self) -> List[Statement]:
        """Get all statements"""
        return self.statement_repository.find_all()

    def get_statement_by_id(self, statement_id: UUID) -> Optional[Statement]:
        """Get a statement by ID"""
        return self.statement_repository.find_by_id(statement_id)

    def delete_statement_with_transactions(self, statement_id: UUID) -> dict:
        """
        Delete a statement and all its associated transactions in a single atomic operation.

        Args:
            statement_id: UUID of the statement to delete

        Returns:
            Dictionary with transaction count and success message

        Raises:
            ValueError: If statement doesn't exist
        """
        # Check if statement exists first
        statement = self.statement_repository.find_by_id(statement_id)
        if not statement:
            raise ValueError(f"Statement with ID {statement_id} not found")

        # Delete all transactions for this statement first
        # This must be done first due to foreign key constraints
        transaction_count = self.transaction_repository.delete_by_statement_id(statement_id)

        # Then delete the statement
        self.statement_repository.delete(statement_id)

        # Note: Transaction commit happens at the dependency injection level
        # through ExternalDependencies.cleanup()

        return {
            "message": f"Statement deleted successfully. {transaction_count} transactions were also deleted.",
            "transaction_count": transaction_count,
        }
