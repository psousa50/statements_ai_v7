from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.domain.models.transaction_categorization import CategorizationSource, TransactionCategorization


class TransactionCategorizationManagementService:
    """
    Service layer for transaction categorization management operations.
    NOTE: This service is deprecated. Enhancement rules are now managed through TransactionRuleEnhancementService.
    Keeping this for API compatibility until migration is complete.
    """

    def __init__(self):
        # No longer requires repository - this is a legacy service
        pass

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
        """Legacy method - returns empty results. Use enhancement rules instead."""
        return ([], 0)

    def get_rule_by_id(self, rule_id: UUID) -> Optional[TransactionCategorization]:
        """Legacy method - returns None. Use enhancement rules instead."""
        return None

    def create_rule(
        self,
        normalized_description: str,
        category_id: UUID,
        source: CategorizationSource,
    ) -> TransactionCategorization:
        """Legacy method - not implemented. Use enhancement rules instead."""
        raise NotImplementedError("Use enhancement rules instead of categorization rules")

    def update_rule(
        self,
        rule_id: UUID,
        normalized_description: str,
        category_id: UUID,
        source: CategorizationSource,
    ) -> Optional[TransactionCategorization]:
        """Legacy method - not implemented. Use enhancement rules instead."""
        raise NotImplementedError("Use enhancement rules instead of categorization rules")

    def delete_rule(self, rule_id: UUID) -> bool:
        """Legacy method - returns False. Use enhancement rules instead."""
        return False

    def get_statistics(self) -> Dict[str, int]:
        """Legacy method - returns empty stats. Use enhancement rules instead."""
        return {"total_rules": 0, "manual_rules": 0, "ai_rules": 0}

    def get_enhanced_statistics(self) -> Dict:
        """Legacy method - returns empty stats. Use enhancement rules instead."""
        return {"unused_rules": [], "category_usage": [], "transaction_counts": {}}

    def bulk_delete_unused_rules(self) -> int:
        """Legacy method - returns 0. Use enhancement rules instead."""
        return 0
