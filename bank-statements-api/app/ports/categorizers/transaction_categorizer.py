from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.transaction import Transaction


class TransactionCategorizer(ABC):
    @abstractmethod
    def categorize(self, transaction: Transaction) -> UUID:
        pass
