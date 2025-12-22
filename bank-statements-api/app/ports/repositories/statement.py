from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.models.statement import Statement


class StatementRepository(ABC):
    @abstractmethod
    def save(
        self,
        account_id: UUID,
        filename: str,
        file_type: str,
        content: bytes,
    ) -> Statement:
        pass

    @abstractmethod
    def find_by_id(self, statement_id: UUID, user_id: UUID) -> Optional[Statement]:
        pass

    @abstractmethod
    def find_by_account_id(self, account_id: UUID, user_id: UUID) -> list[Statement]:
        pass

    @abstractmethod
    def find_all(self, user_id: UUID) -> list[Statement]:
        pass

    @abstractmethod
    def delete(self, statement_id: UUID, user_id: UUID) -> None:
        pass

    @abstractmethod
    def update_transaction_statistics(self, statement_id: UUID) -> None:
        pass
