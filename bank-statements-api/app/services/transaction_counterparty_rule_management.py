from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.domain.models.transaction_counterparty_rule import CounterpartyRuleSource, TransactionCounterpartyRule


class TransactionCounterpartyRuleManagementService:
    """
    Service for managing transaction counterparty rules.
    NOTE: This service is deprecated. Enhancement rules are now managed through TransactionRuleEnhancementService.
    Keeping this for API compatibility until migration is complete.
    """

    def __init__(self):
        # No longer requires repository - this is a legacy service
        pass

    def create_rule(
        self,
        normalized_description: str,
        counterparty_account_id: UUID,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        source: CounterpartyRuleSource = CounterpartyRuleSource.MANUAL,
    ) -> TransactionCounterpartyRule:
        """Legacy method - not implemented. Use enhancement rules instead."""
        raise NotImplementedError("Use enhancement rules instead of counterparty rules")

    def get_rule_by_id(self, rule_id: UUID) -> Optional[TransactionCounterpartyRule]:
        """Legacy method - returns None. Use enhancement rules instead."""
        return None

    def get_rule_by_description(self, normalized_description: str) -> Optional[TransactionCounterpartyRule]:
        """Legacy method - returns None. Use enhancement rules instead."""
        return None

    def get_all_rules(self) -> List[TransactionCounterpartyRule]:
        """Legacy method - returns empty list. Use enhancement rules instead."""
        return []

    def update_rule(
        self,
        rule_id: UUID,
        normalized_description: str,
        counterparty_account_id: UUID,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        source: CounterpartyRuleSource = CounterpartyRuleSource.MANUAL,
    ) -> Optional[TransactionCounterpartyRule]:
        """Legacy method - not implemented. Use enhancement rules instead."""
        raise NotImplementedError("Use enhancement rules instead of counterparty rules")

    def delete_rule(self, rule_id: UUID) -> bool:
        """Legacy method - returns False. Use enhancement rules instead."""
        return False
