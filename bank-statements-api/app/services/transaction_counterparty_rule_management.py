from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.domain.models.transaction_counterparty_rule import CounterpartyRuleSource, TransactionCounterpartyRule
from app.ports.repositories.transaction_counterparty_rule import TransactionCounterpartyRuleRepository


class TransactionCounterpartyRuleManagementService:
    """Service for managing transaction counterparty rules"""

    def __init__(self, repository: TransactionCounterpartyRuleRepository):
        self.repository = repository

    def create_rule(
        self,
        normalized_description: str,
        counterparty_account_id: UUID,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        source: CounterpartyRuleSource = CounterpartyRuleSource.MANUAL,
    ) -> TransactionCounterpartyRule:
        """Create a new counterparty rule"""
        rule = TransactionCounterpartyRule(
            normalized_description=normalized_description,
            counterparty_account_id=counterparty_account_id,
            min_amount=min_amount,
            max_amount=max_amount,
            source=source,
        )
        return self.repository.create(rule)

    def get_rule_by_id(self, rule_id: UUID) -> Optional[TransactionCounterpartyRule]:
        """Get a rule by its ID"""
        return self.repository.get_by_id(rule_id)

    def get_rule_by_description(self, normalized_description: str) -> Optional[TransactionCounterpartyRule]:
        """Get a rule by normalized description"""
        return self.repository.get_by_normalized_description(normalized_description)

    def get_all_rules(self) -> List[TransactionCounterpartyRule]:
        """Get all counterparty rules"""
        return self.repository.get_all()

    def update_rule(
        self,
        rule_id: UUID,
        normalized_description: str,
        counterparty_account_id: UUID,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        source: CounterpartyRuleSource = CounterpartyRuleSource.MANUAL,
    ) -> Optional[TransactionCounterpartyRule]:
        """Update an existing counterparty rule"""
        rule = self.repository.get_by_id(rule_id)
        if rule:
            rule.normalized_description = normalized_description
            rule.counterparty_account_id = counterparty_account_id
            rule.min_amount = min_amount
            rule.max_amount = max_amount
            rule.source = source
            return self.repository.update(rule)
        return None

    def delete_rule(self, rule_id: UUID) -> bool:
        """Delete a counterparty rule"""
        rule = self.repository.get_by_id(rule_id)
        if rule:
            self.repository.delete(rule_id)
            return True
        return False
