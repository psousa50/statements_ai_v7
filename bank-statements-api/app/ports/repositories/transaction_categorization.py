from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.transaction_categorization import CategorizationSource, TransactionCategorization


class TransactionCategorizationRepository(ABC):
    """
    Port (interface) for transaction categorization repository operations.
    Following Hexagonal Architecture pattern.
    """

    @abstractmethod
    def get_categories_by_normalized_descriptions(
        self, normalized_descriptions: List[str], batch_size: int = 100
    ) -> Dict[str, UUID]:
        """
        Get category mappings for normalized descriptions.

        Args:
            normalized_descriptions: List of normalized transaction descriptions
            batch_size: Size of batches for processing large lists

        Returns:
            Dictionary mapping normalized_description -> category_id for found matches
        """
        pass

    @abstractmethod
    def create_rule(
        self,
        normalized_description: str,
        category_id: UUID,
        source: CategorizationSource,
    ) -> TransactionCategorization:
        """Create a new categorization rule"""
        pass

    @abstractmethod
    def get_rule_by_normalized_description(self, normalized_description: str) -> Optional[TransactionCategorization]:
        """Get a categorization rule by normalized description"""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, int]:
        """Get repository statistics for monitoring and analytics"""
        pass
