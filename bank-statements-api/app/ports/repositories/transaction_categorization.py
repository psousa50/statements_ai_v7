from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
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

    @abstractmethod
    def get_rules_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        description_search: Optional[str] = None,
        category_ids: Optional[List[str]] = None,
        source: Optional[CategorizationSource] = None,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
    ) -> Tuple[List[TransactionCategorization], int]:
        """
        Get paginated categorization rules with filtering and sorting.

        Args:
            page: Page number (1-based)
            page_size: Number of rules per page
            description_search: Filter by normalized description
            category_ids: Filter by category IDs
            source: Filter by categorization source
            sort_field: Field to sort by (normalized_description, category, usage, source, created_at)
            sort_direction: Sort direction (asc or desc)

        Returns:
            Tuple of (rules_list, total_count)
        """
        pass

    @abstractmethod
    def get_rule_by_id(self, rule_id: UUID) -> Optional[TransactionCategorization]:
        """Get a categorization rule by ID"""
        pass

    @abstractmethod
    def update_rule(
        self,
        rule_id: UUID,
        normalized_description: str,
        category_id: UUID,
        source: CategorizationSource,
    ) -> Optional[TransactionCategorization]:
        """Update an existing categorization rule"""
        pass

    @abstractmethod
    def delete_rule(self, rule_id: UUID) -> bool:
        """Delete a categorization rule"""
        pass

    @abstractmethod
    def get_enhanced_statistics(self) -> Dict:
        """Get enhanced statistics with category usage and transaction counts"""
        pass
