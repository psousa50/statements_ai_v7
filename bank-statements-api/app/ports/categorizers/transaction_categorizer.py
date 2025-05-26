from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.models.categorization import CategorizationResult
from app.domain.models.transaction import Transaction


class TransactionCategorizer(ABC):
    @abstractmethod
    def categorize(self, transactions: List[Transaction]) -> List[CategorizationResult]:
        """Categorize a batch of transactions with detailed results"""
        pass
