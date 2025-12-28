from typing import Any, Dict, List, Optional
from uuid import UUID

from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.ports.repositories.account import AccountRepository
from app.ports.repositories.category import CategoryRepository
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.transaction import TransactionRepository


class EnhancementRuleManagementService:
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
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
        rule_status_filter: Optional[str] = None,
        sort_field: str = "created_at",
        sort_direction: str = "desc",
    ) -> Dict[str, Any]:
        rules = self.enhancement_rule_repository.get_all(
            user_id=user_id,
            limit=limit,
            offset=offset,
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
            rule_status_filter=rule_status_filter,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

        total = self.enhancement_rule_repository.count(
            user_id=user_id,
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
            rule_status_filter=rule_status_filter,
        )

        for rule in rules:
            rule.transaction_count = self._get_rule_transaction_count(rule)
            rule.pending_transaction_count = self._get_rule_pending_count(rule)

        return {
            "rules": rules,
            "total": total,
        }

    def get_rule(self, rule_id: UUID, user_id: UUID) -> Optional[EnhancementRule]:
        rule = self.enhancement_rule_repository.find_by_id(rule_id, user_id)

        if rule:
            rule.transaction_count = self._get_rule_transaction_count(rule)
            rule.pending_transaction_count = self._get_rule_pending_count(rule)

        return rule

    def create_rule(
        self,
        user_id: UUID,
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
        if category_id:
            category = self.category_repository.get_by_id(category_id, user_id)
            if not category:
                raise ValueError(f"Category with ID {category_id} not found")

        if counterparty_account_id:
            account = self.account_repository.get_by_id(counterparty_account_id, user_id)
            if not account:
                raise ValueError(f"Account with ID {counterparty_account_id} not found")

        if min_amount is not None and max_amount is not None and min_amount > max_amount:
            raise ValueError("min_amount cannot be greater than max_amount")

        rule = EnhancementRule(
            user_id=user_id,
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
        user_id: UUID,
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
        rule = self.enhancement_rule_repository.find_by_id(rule_id, user_id)
        if not rule:
            return None

        if category_id:
            category = self.category_repository.get_by_id(category_id, user_id)
            if not category:
                raise ValueError(f"Category with ID {category_id} not found")

        if counterparty_account_id:
            account = self.account_repository.get_by_id(counterparty_account_id, user_id)
            if not account:
                raise ValueError(f"Account with ID {counterparty_account_id} not found")

        if min_amount is not None and max_amount is not None and min_amount > max_amount:
            raise ValueError("min_amount cannot be greater than max_amount")

        rule.normalized_description_pattern = normalized_description_pattern
        rule.match_type = match_type
        rule.category_id = category_id
        rule.counterparty_account_id = counterparty_account_id
        rule.min_amount = min_amount
        rule.max_amount = max_amount
        rule.start_date = start_date
        rule.end_date = end_date
        rule.source = source

        updated_rule = self.enhancement_rule_repository.save(rule)

        if apply_to_existing:
            self.apply_rule_to_existing_transactions(rule_id, user_id)

        return updated_rule

    def delete_rule(self, rule_id: UUID, user_id: UUID) -> bool:
        rule = self.enhancement_rule_repository.find_by_id(rule_id, user_id)
        if not rule:
            return False

        self.enhancement_rule_repository.delete(rule)
        return True

    def cleanup_unused_rules(self, user_id: UUID) -> Dict[str, Any]:
        all_rules = self.enhancement_rule_repository.get_all(user_id=user_id, limit=10000)
        unused_rules = []

        for rule in all_rules:
            transaction_count = self._get_rule_transaction_count(rule)
            if transaction_count == 0:
                unused_rules.append(rule)

        for rule in unused_rules:
            self.enhancement_rule_repository.delete(rule)

        return {
            "deleted_count": len(unused_rules),
            "message": f"Deleted {len(unused_rules)} unused enhancement rules",
        }

    def get_stats(self, user_id: UUID) -> Dict[str, Any]:
        all_rules = self.enhancement_rule_repository.get_all(user_id=user_id, limit=10000)

        total_rules = len(all_rules)
        manual_rules = len([r for r in all_rules if r.source == EnhancementRuleSource.MANUAL])
        auto_rules = len([r for r in all_rules if r.source == EnhancementRuleSource.AUTO])

        category_only_rules = len([r for r in all_rules if r.category_id and not r.counterparty_account_id])
        counterparty_only_rules = len([r for r in all_rules if r.counterparty_account_id and not r.category_id])
        combined_rules = len([r for r in all_rules if r.category_id and r.counterparty_account_id])

        total_transactions_enhanced = 0
        transactions_with_manual_rules = 0
        transactions_with_auto_rules = 0

        for rule in all_rules:
            count = self._get_rule_transaction_count(rule)
            total_transactions_enhanced += count

            if rule.source == EnhancementRuleSource.MANUAL:
                transactions_with_manual_rules += count
            else:
                transactions_with_auto_rules += count

        rules_with_counts = []
        for rule in all_rules:
            count = self._get_rule_transaction_count(rule)
            rules_with_counts.append((rule, count))

        top_rules = sorted(rules_with_counts, key=lambda x: x[1], reverse=True)[:10]
        unused_rules = [r for r, count in rules_with_counts if count == 0]

        return {
            "summary": {
                "total_rules": total_rules,
                "manual_rules": manual_rules,
                "auto_rules": auto_rules,
                "category_only_rules": category_only_rules,
                "counterparty_only_rules": counterparty_only_rules,
                "combined_rules": combined_rules,
                "total_transactions_enhanced": total_transactions_enhanced,
                "transactions_with_manual_rules": transactions_with_manual_rules,
                "transactions_with_auto_rules": transactions_with_auto_rules,
            },
            "top_rules_by_usage": [
                {
                    "rule_id": str(rule.id),
                    "normalized_description": rule.normalized_description_pattern,
                    "category_name": rule.category.name if rule.category else None,
                    "counterparty_name": rule.counterparty_account.name if rule.counterparty_account else None,
                    "transaction_count": count,
                    "source": rule.source.value,
                    "rule_type": rule.rule_type,
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
                    "rule_type": rule.rule_type,
                }
                for rule in unused_rules
            ],
        }

    def _get_rule_transaction_count(self, rule: EnhancementRule) -> int:
        try:
            is_unconfigured = not rule.category_id and not rule.counterparty_account_id
            return self.transaction_repository.count_matching_rule(rule, uncategorized_only=is_unconfigured)
        except Exception:
            return 0

    def _get_rule_pending_count(self, rule: EnhancementRule) -> int:
        try:
            return self.transaction_repository.count_pending_for_rule(rule)
        except Exception:
            return 0

    def get_matching_transactions_count(self, rule_id: UUID, user_id: UUID) -> Dict[str, Any]:
        rule = self.enhancement_rule_repository.find_by_id(rule_id, user_id)
        if not rule:
            raise ValueError(f"Enhancement rule with ID {rule_id} not found")

        count = self.transaction_repository.count_matching_rule(rule)

        return {
            "count": count,
            "date_range": None,
            "amount_range": None,
        }

    def preview_matching_transactions_count(self, rule_preview: Any, user_id: UUID) -> Dict[str, Any]:
        if rule_preview.category_id:
            category = self.category_repository.get_by_id(rule_preview.category_id, user_id)
            if not category:
                raise ValueError(f"Category with ID {rule_preview.category_id} not found")

        if rule_preview.counterparty_account_id:
            account = self.account_repository.get_by_id(rule_preview.counterparty_account_id, user_id)
            if not account:
                raise ValueError(f"Account with ID {rule_preview.counterparty_account_id} not found")

        temp_rule = EnhancementRule(
            user_id=user_id,
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

        count = self.transaction_repository.count_matching_rule(temp_rule)

        return {
            "count": count,
            "date_range": None,
            "amount_range": None,
        }

    def apply_rule_to_existing_transactions(self, rule_id: UUID, user_id: UUID) -> int:
        from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus

        rule = self.enhancement_rule_repository.find_by_id(rule_id, user_id)
        if not rule:
            raise ValueError(f"Enhancement rule with ID {rule_id} not found")

        total_updated = 0
        page = 1
        batch_size = 1000

        while True:
            matching_transactions = self.transaction_repository.find_transactions_matching_rule(
                rule=rule, page=page, page_size=batch_size
            )

            if not matching_transactions:
                break

            for transaction in matching_transactions:
                updated = False

                if rule.category_id and transaction.categorization_status in [
                    CategorizationStatus.UNCATEGORIZED,
                    CategorizationStatus.RULE_BASED,
                    CategorizationStatus.FAILURE,
                ]:
                    transaction.category_id = rule.category_id
                    transaction.categorization_status = CategorizationStatus.RULE_BASED
                    updated = True

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

            if total_updated > 10000:
                break

        return total_updated
