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
    def find_by_id(self, statement_id: UUID) -> Optional[Statement]:
        pass

    @abstractmethod
    def find_by_account_id(self, account_id: UUID) -> list[Statement]:
        pass
