from abc import ABC, abstractmethod
from typing import List

from app.domain.models.counterparty import CounterpartyResult
from app.domain.models.transaction import Transaction


class TransactionCounterparty(ABC):
    @abstractmethod
    def identify_counterparty(self, transactions: List[Transaction]) -> List[CounterpartyResult]:
        """Identify counterparty accounts for a batch of transactions with detailed results"""
        pass
