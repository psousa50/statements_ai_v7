from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.transaction_counterparty_rule import TransactionCounterpartyRule


class TransactionCounterpartyRuleRepository(ABC):
    @abstractmethod
    def create(self, rule: TransactionCounterpartyRule) -> TransactionCounterpartyRule:
        """Create a new counterparty rule"""
        pass

    @abstractmethod
    def get_by_id(self, rule_id: UUID) -> Optional[TransactionCounterpartyRule]:
        """Get a rule by its ID"""
        pass

    @abstractmethod
    def get_by_normalized_description(self, normalized_description: str) -> Optional[TransactionCounterpartyRule]:
        """Get a rule by normalized description"""
        pass

    @abstractmethod
    def get_all(self) -> List[TransactionCounterpartyRule]:
        """Get all counterparty rules"""
        pass

    @abstractmethod
    def update(self, rule: TransactionCounterpartyRule) -> TransactionCounterpartyRule:
        """Update a counterparty rule"""
        pass

    @abstractmethod
    def delete(self, rule_id: UUID) -> None:
        """Delete a counterparty rule"""
        pass

    @abstractmethod
    def get_counterparty_accounts_by_normalized_descriptions_and_amounts(
        self, description_amount_pairs: List[tuple[str, Decimal]], batch_size: int = 100
    ) -> Dict[str, UUID]:
        """
        Get counterparty account IDs for normalized descriptions and amounts that match rules.

        Args:
            description_amount_pairs: List of (normalized_description, amount) tuples
            batch_size: Batch size for processing large lists

        Returns:
            Dictionary mapping normalized_description -> counterparty_account_id for found matches
        """
        pass
