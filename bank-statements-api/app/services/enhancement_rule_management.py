"""Enhancement Rule Management Service."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.ports.repositories.account import AccountRepository
from app.ports.repositories.category import CategoryRepository
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.transaction import TransactionRepository


class EnhancementRuleManagementService:
    """Service for managing enhancement rules with business logic."""

    def __init__(
        self,
        enhancement_rule_repository: EnhancementRuleRepository,
        category_repository: CategoryRepository,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
    ):
        self.enhancement_rule_repository = enhancement_rule_repository
        self.category_repository = category_repository
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository

    def list_rules(
        self,
        limit: int = 50,
        offset: int = 0,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
        sort_field: str = "created_at",
        sort_direction: str = "desc",
    ) -> Dict[str, Any]:
        """List enhancement rules with filtering and pagination."""

        # Get rules with filters
        rules = self.enhancement_rule_repository.get_all(
            limit=limit,
            offset=offset,
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

        # Get total count for pagination
        total = self.enhancement_rule_repository.count(
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
        )

        # Populate transaction counts for each rule
        for rule in rules:
            rule.transaction_count = self._get_rule_transaction_count(rule)

        return {
            "rules": rules,
            "total": total,
        }

    def get_rule(self, rule_id: UUID) -> Optional[EnhancementRule]:
        """Get a specific enhancement rule by ID."""
        rule = self.enhancement_rule_repository.find_by_id(rule_id)

        if rule:
            rule.transaction_count = self._get_rule_transaction_count(rule)

        return rule

    def create_rule(
        self,
        normalized_description_pattern: str,
        match_type: MatchType,
        category_id: Optional[UUID] = None,
        counterparty_account_id: Optional[UUID] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source: EnhancementRuleSource = EnhancementRuleSource.MANUAL,
    ) -> EnhancementRule:
        """Create a new enhancement rule with validation."""

        # Validate that at least one enhancement is specified
        if not category_id and not counterparty_account_id:
            raise ValueError("Must specify either category_id or counterparty_account_id (or both)")

        # Validate category exists if specified
        if category_id:
            category = self.category_repository.get_by_id(category_id)
            if not category:
                raise ValueError(f"Category with ID {category_id} not found")

        # Validate counterparty account exists if specified
        if counterparty_account_id:
            account = self.account_repository.get_by_id(counterparty_account_id)
            if not account:
                raise ValueError(f"Account with ID {counterparty_account_id} not found")

        # Validate amount constraints
        if min_amount is not None and max_amount is not None and min_amount > max_amount:
            raise ValueError("min_amount cannot be greater than max_amount")

        # Check for duplicate rules
        existing_rule = self.enhancement_rule_repository.find_by_normalized_description(normalized_description_pattern)
        if existing_rule:
            raise ValueError(f"Rule with pattern '{normalized_description_pattern}' already exists")

        # Create the rule
        rule = EnhancementRule(
            normalized_description_pattern=normalized_description_pattern,
            match_type=match_type,
            category_id=category_id,
            counterparty_account_id=counterparty_account_id,
            min_amount=min_amount,
            max_amount=max_amount,
            start_date=start_date,
            end_date=end_date,
            source=source,
        )

        return self.enhancement_rule_repository.save(rule)

    def update_rule(
        self,
        rule_id: UUID,
        normalized_description_pattern: str,
        match_type: MatchType,
        category_id: Optional[UUID] = None,
        counterparty_account_id: Optional[UUID] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source: EnhancementRuleSource = EnhancementRuleSource.MANUAL,
        apply_to_existing: bool = False,
    ) -> Optional[EnhancementRule]:
        """Update an existing enhancement rule with validation."""

        # Get existing rule
        rule = self.enhancement_rule_repository.find_by_id(rule_id)
        if not rule:
            return None

        # Validate that at least one enhancement is specified
        if not category_id and not counterparty_account_id:
            raise ValueError("Must specify either category_id or counterparty_account_id (or both)")

        # Validate category exists if specified
        if category_id:
            category = self.category_repository.get_by_id(category_id)
            if not category:
                raise ValueError(f"Category with ID {category_id} not found")

        # Validate counterparty account exists if specified
        if counterparty_account_id:
            account = self.account_repository.get_by_id(counterparty_account_id)
            if not account:
                raise ValueError(f"Account with ID {counterparty_account_id} not found")

        # Validate amount constraints
        if min_amount is not None and max_amount is not None and min_amount > max_amount:
            raise ValueError("min_amount cannot be greater than max_amount")

        # Check for duplicate rules (excluding current rule)
        if normalized_description_pattern != rule.normalized_description_pattern:
            existing_rule = self.enhancement_rule_repository.find_by_normalized_description(normalized_description_pattern)
            if existing_rule and existing_rule.id != rule_id:
                raise ValueError(f"Rule with pattern '{normalized_description_pattern}' already exists")

        # Update the rule
        rule.normalized_description_pattern = normalized_description_pattern
        rule.match_type = match_type
        rule.category_id = category_id
        rule.counterparty_account_id = counterparty_account_id
        rule.min_amount = min_amount
        rule.max_amount = max_amount
        rule.start_date = start_date
        rule.end_date = end_date
        rule.source = source

        # Save the updated rule
        updated_rule = self.enhancement_rule_repository.save(rule)

        # Apply to existing transactions if requested
        if apply_to_existing:
            self.apply_rule_to_existing_transactions(rule_id)

        return updated_rule

    def delete_rule(self, rule_id: UUID) -> bool:
        """Delete an enhancement rule."""
        rule = self.enhancement_rule_repository.find_by_id(rule_id)
        if not rule:
            return False

        self.enhancement_rule_repository.delete(rule)
        return True

    def cleanup_unused_rules(self) -> Dict[str, Any]:
        """Delete rules that haven't been used to categorize any transactions."""

        all_rules = self.enhancement_rule_repository.get_all()
        unused_rules = []

        for rule in all_rules:
            transaction_count = self._get_rule_transaction_count(rule)
            if transaction_count == 0:
                unused_rules.append(rule)

        # Delete unused rules
        for rule in unused_rules:
            self.enhancement_rule_repository.delete(rule)

        return {
            "deleted_count": len(unused_rules),
            "message": f"Deleted {len(unused_rules)} unused enhancement rules",
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about enhancement rules."""

        # Get all rules
        all_rules = self.enhancement_rule_repository.get_all()

        # Basic counts
        total_rules = len(all_rules)
        manual_rules = len([r for r in all_rules if r.source == EnhancementRuleSource.MANUAL])
        ai_rules = len([r for r in all_rules if r.source == EnhancementRuleSource.AI])

        # Rule type counts
        category_only_rules = len([r for r in all_rules if r.category_id and not r.counterparty_account_id])
        counterparty_only_rules = len([r for r in all_rules if r.counterparty_account_id and not r.category_id])
        combined_rules = len([r for r in all_rules if r.category_id and r.counterparty_account_id])

        # Get transaction counts
        total_transactions_enhanced = 0
        transactions_with_manual_rules = 0
        transactions_with_ai_rules = 0

        for rule in all_rules:
            count = self._get_rule_transaction_count(rule)
            total_transactions_enhanced += count

            if rule.source == EnhancementRuleSource.MANUAL:
                transactions_with_manual_rules += count
            else:
                transactions_with_ai_rules += count

        # Top rules by usage
        rules_with_counts = []
        for rule in all_rules:
            count = self._get_rule_transaction_count(rule)
            rules_with_counts.append((rule, count))

        top_rules = sorted(
            rules_with_counts,
            key=lambda x: x[1],
            reverse=True,
        )[:10]
        unused_rules = [r for r, count in rules_with_counts if count == 0]

        return {
            "summary": {
                "total_rules": total_rules,
                "manual_rules": manual_rules,
                "ai_rules": ai_rules,
                "category_only_rules": category_only_rules,
                "counterparty_only_rules": counterparty_only_rules,
                "combined_rules": combined_rules,
                "total_transactions_enhanced": total_transactions_enhanced,
                "transactions_with_manual_rules": transactions_with_manual_rules,
                "transactions_with_ai_rules": transactions_with_ai_rules,
            },
            "top_rules_by_usage": [
                {
                    "rule_id": str(rule.id),
                    "normalized_description": rule.normalized_description_pattern,
                    "category_name": rule.category.name if rule.category else None,
                    "counterparty_name": rule.counterparty_account.name if rule.counterparty_account else None,
                    "transaction_count": count,
                    "source": rule.source.value,
                    "rule_type": self._get_rule_type_display(rule),
                }
                for rule, count in top_rules
            ],
            "unused_rules": [
                {
                    "rule_id": str(rule.id),
                    "normalized_description": rule.normalized_description_pattern,
                    "category_name": rule.category.name if rule.category else None,
                    "counterparty_name": rule.counterparty_account.name if rule.counterparty_account else None,
                    "source": rule.source.value,
                    "created_at": rule.created_at.isoformat(),
                    "rule_type": self._get_rule_type_display(rule),
                }
                for rule in unused_rules
            ],
        }

    def _get_rule_transaction_count(self, rule: EnhancementRule) -> int:
        """Get the number of transactions that would match this rule."""
        # This is a simplified implementation
        # In a real system, you might want to cache these counts or use more efficient queries
        try:
            return self.transaction_repository.count_matching_rule(rule)
        except Exception:
            # Fallback if the repository doesn't have this method yet
            return 0

    def _get_rule_type_display(self, rule: EnhancementRule) -> str:
        """Get a display string for the rule type."""
        has_category = rule.category_id is not None
        has_counterparty = rule.counterparty_account_id is not None

        if has_category and has_counterparty:
            return "Category + Counterparty"
        elif has_category:
            return "Category Only"
        elif has_counterparty:
            return "Counterparty Only"
        else:
            return "Invalid Rule"

    def get_matching_transactions_count(self, rule_id: UUID) -> Dict[str, Any]:
        """Get count of transactions that would match this enhancement rule."""
        # Get the rule
        rule = self.enhancement_rule_repository.find_by_id(rule_id)
        if not rule:
            raise ValueError(f"Enhancement rule with ID {rule_id} not found")

        # Get the count
        count = self.transaction_repository.count_matching_rule(rule)

        # TODO: Add date_range and amount_range calculation if needed
        return {
            "count": count,
            "date_range": None,
            "amount_range": None,
        }

    def preview_matching_transactions_count(self, rule_preview: Any) -> Dict[str, Any]:
        """Preview count of transactions that would match the given enhancement rule criteria."""
        # Note: We allow preview without enhancements to show matching transaction counts
        # The actual rule creation will still require at least one enhancement

        # Validate category exists if provided
        if rule_preview.category_id:
            category = self.category_repository.find_by_id(rule_preview.category_id)
            if not category:
                raise ValueError(f"Category with ID {rule_preview.category_id} not found")

        # Validate counterparty account exists if provided
        if rule_preview.counterparty_account_id:
            account = self.account_repository.find_by_id(rule_preview.counterparty_account_id)
            if not account:
                raise ValueError(f"Account with ID {rule_preview.counterparty_account_id} not found")

        # Create a temporary rule object for counting (not persisted)
        temp_rule = EnhancementRule(
            normalized_description_pattern=rule_preview.normalized_description_pattern,
            match_type=rule_preview.match_type,
            category_id=rule_preview.category_id,
            counterparty_account_id=rule_preview.counterparty_account_id,
            min_amount=rule_preview.min_amount,
            max_amount=rule_preview.max_amount,
            start_date=rule_preview.start_date,
            end_date=rule_preview.end_date,
            source=rule_preview.source,
        )

        # Get the count using the temporary rule
        count = self.transaction_repository.count_matching_rule(temp_rule)

        # TODO: Add date_range and amount_range calculation if needed
        return {
            "count": count,
            "date_range": None,
            "amount_range": None,
        }

    def apply_rule_to_existing_transactions(self, rule_id: UUID) -> int:
        """Apply an enhancement rule to all existing matching transactions with batch processing."""
        from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus

        # Get the rule
        rule = self.enhancement_rule_repository.find_by_id(rule_id)
        if not rule:
            raise ValueError(f"Enhancement rule with ID {rule_id} not found")

        total_updated = 0
        page = 1
        batch_size = 1000

        while True:
            # Get transactions matching the rule using pagination
            matching_transactions = self.transaction_repository.find_transactions_matching_rule(
                rule=rule, page=page, page_size=batch_size
            )

            if not matching_transactions:
                break  # No more transactions to process

            # Apply selective updates based on current status
            for transaction in matching_transactions:
                updated = False

                # Only update category if transaction is UNCATEGORIZED, RULE_BASED, or FAILURE
                # Never overwrite MANUAL categorizations
                if rule.category_id and transaction.categorization_status in [
                    CategorizationStatus.UNCATEGORIZED,
                    CategorizationStatus.RULE_BASED,
                    CategorizationStatus.FAILURE,
                ]:
                    transaction.category_id = rule.category_id
                    transaction.categorization_status = CategorizationStatus.RULE_BASED
                    updated = True

                # Only update counterparty if it's currently unprocessed or was rule-based
                # Never overwrite MANUAL assignments
                if rule.counterparty_account_id and transaction.counterparty_status in [
                    CounterpartyStatus.UNPROCESSED,
                    CounterpartyStatus.RULE_BASED,
                    CounterpartyStatus.FAILURE,
                ]:
                    transaction.counterparty_account_id = rule.counterparty_account_id
                    transaction.counterparty_status = CounterpartyStatus.RULE_BASED
                    updated = True

                if updated:
                    self.transaction_repository.update(transaction)
                    total_updated += 1

            page += 1

            # Optional: For very large updates, this could break and continue as background job
            # For now, let's process everything synchronously
            if total_updated > 10000:  # Safety limit
                break

        return total_updated
