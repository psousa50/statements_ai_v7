from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.domain.models.transaction_categorization import CategorizationSource, TransactionCategorization
from app.ports.repositories.transaction_categorization import TransactionCategorizationRepository


class TransactionCategorizationManagementService:
    """
    Service layer for transaction categorization management operations.
    Encapsulates business logic following Clean Architecture principles.
    """

    def __init__(self, repository: TransactionCategorizationRepository):
        self.repository = repository

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
        Get paginated categorization rules with filtering, sorting and business logic validation.

        Args:
            page: Page number (1-based)
            page_size: Number of rules per page (max 100)
            description_search: Filter by normalized description
            category_ids: Filter by category IDs
            source: Filter by categorization source
            sort_field: Field to sort by (normalized_description, category, usage, source, created_at)
            sort_direction: Sort direction (asc or desc)

        Returns:
            Tuple of (rules_list, total_count)
        """
        # Validate and sanitize inputs
        page = max(1, page)
        page_size = min(max(1, page_size), 100)  # Limit page size to prevent performance issues

        if description_search:
            description_search = description_search.strip()
            if len(description_search) < 2:  # Minimum search length
                description_search = None

        # Validate sort parameters
        if sort_field:
            valid_sort_fields = {"normalized_description", "category", "usage", "source", "created_at"}
            if sort_field not in valid_sort_fields:
                sort_field = "created_at"  # Default to created_at for invalid fields

        if sort_direction:
            sort_direction = sort_direction.lower()
            if sort_direction not in {"asc", "desc"}:
                sort_direction = "desc"  # Default to desc for invalid directions

        return self.repository.get_rules_paginated(
            page=page,
            page_size=page_size,
            description_search=description_search,
            category_ids=category_ids,
            source=source,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

    def get_rule_by_id(self, rule_id: UUID) -> Optional[TransactionCategorization]:
        """Get a categorization rule by ID."""
        return self.repository.get_rule_by_id(rule_id)

    def create_rule(
        self,
        normalized_description: str,
        category_id: UUID,
        source: CategorizationSource,
    ) -> TransactionCategorization:
        """
        Create a new categorization rule with business logic validation.

        Args:
            normalized_description: The normalized transaction description
            category_id: The category to assign to this rule
            source: The source of the categorization (MANUAL or AI)

        Returns:
            The created TransactionCategorization

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        normalized_description = normalized_description.strip().lower()
        if not normalized_description:
            raise ValueError("Normalized description cannot be empty")

        if len(normalized_description) < 2:
            raise ValueError("Normalized description must be at least 2 characters")

        # Check if rule already exists
        existing_rule = self.repository.get_rule_by_normalized_description(normalized_description)
        if existing_rule:
            raise ValueError(f"Rule for '{normalized_description}' already exists")

        return self.repository.create_rule(
            normalized_description=normalized_description,
            category_id=category_id,
            source=source,
        )

    def update_rule(
        self,
        rule_id: UUID,
        normalized_description: str,
        category_id: UUID,
        source: CategorizationSource,
    ) -> Optional[TransactionCategorization]:
        """
        Update an existing categorization rule with business logic validation.

        Args:
            rule_id: The ID of the rule to update
            normalized_description: The new normalized transaction description
            category_id: The new category to assign to this rule
            source: The new source of the categorization

        Returns:
            The updated TransactionCategorization or None if not found

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        normalized_description = normalized_description.strip().lower()
        if not normalized_description:
            raise ValueError("Normalized description cannot be empty")

        if len(normalized_description) < 2:
            raise ValueError("Normalized description must be at least 2 characters")

        # Check if we're trying to update to a description that already exists (for a different rule)
        existing_rule = self.repository.get_rule_by_normalized_description(normalized_description)
        if existing_rule and existing_rule.id != rule_id:
            raise ValueError(f"Rule for '{normalized_description}' already exists")

        return self.repository.update_rule(
            rule_id=rule_id,
            normalized_description=normalized_description,
            category_id=category_id,
            source=source,
        )

    def delete_rule(self, rule_id: UUID) -> bool:
        """
        Delete a categorization rule.

        Args:
            rule_id: The ID of the rule to delete

        Returns:
            True if the rule was deleted, False if it didn't exist
        """
        return self.repository.delete_rule(rule_id)

    def get_statistics(self) -> Dict[str, int]:
        """Get basic categorization statistics."""
        return self.repository.get_statistics()

    def get_enhanced_statistics(self) -> Dict:
        """Get enhanced statistics with category usage and transaction counts."""
        return self.repository.get_enhanced_statistics()

    def bulk_delete_unused_rules(self) -> int:
        """
        Delete all rules that are not being used by any transactions.

        Returns:
            Number of rules deleted
        """
        stats = self.get_enhanced_statistics()
        unused_rules = stats.get("unused_rules", [])

        deleted_count = 0
        for rule in unused_rules:
            rule_id = UUID(rule["rule_id"])
            if self.repository.delete_rule(rule_id):
                deleted_count += 1

        return deleted_count
