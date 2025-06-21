from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.domain.models.transaction_counterparty_rule import TransactionCounterpartyRule
from app.ports.repositories.transaction_counterparty_rule import TransactionCounterpartyRuleRepository


class SQLAlchemyTransactionCounterpartyRuleRepository(TransactionCounterpartyRuleRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, rule: TransactionCounterpartyRule) -> TransactionCounterpartyRule:
        self.db_session.add(rule)
        self.db_session.commit()
        self.db_session.refresh(rule)
        return rule

    def get_by_id(self, rule_id: UUID) -> Optional[TransactionCounterpartyRule]:
        return self.db_session.query(TransactionCounterpartyRule).filter(TransactionCounterpartyRule.id == rule_id).first()

    def get_by_normalized_description(self, normalized_description: str) -> Optional[TransactionCounterpartyRule]:
        return (
            self.db_session.query(TransactionCounterpartyRule)
            .filter(TransactionCounterpartyRule.normalized_description == normalized_description)
            .first()
        )

    def get_all(self) -> List[TransactionCounterpartyRule]:
        return self.db_session.query(TransactionCounterpartyRule).all()

    def update(self, rule: TransactionCounterpartyRule) -> TransactionCounterpartyRule:
        self.db_session.commit()
        self.db_session.refresh(rule)
        return rule

    def delete(self, rule_id: UUID) -> None:
        rule = self.get_by_id(rule_id)
        if rule:
            self.db_session.delete(rule)
            self.db_session.commit()

    def get_counterparty_accounts_by_normalized_descriptions_and_amounts(
        self, description_amount_pairs: List[tuple[str, Decimal]], batch_size: int = 100
    ) -> Dict[str, UUID]:
        """
        Get counterparty account IDs for normalized descriptions and amounts that match rules.
        Matches on normalized_description and amount range (if specified).
        """
        if not description_amount_pairs:
            return {}

        result = {}

        # Process in batches
        for i in range(0, len(description_amount_pairs), batch_size):
            batch = description_amount_pairs[i : i + batch_size]

            # Build conditions for this batch
            conditions = []
            for description, amount in batch:
                # Match normalized description and amount range
                desc_condition = TransactionCounterpartyRule.normalized_description == description

                # Amount range conditions
                amount_conditions = []

                # If min_amount is null or amount >= min_amount
                min_condition = or_(
                    TransactionCounterpartyRule.min_amount.is_(None), TransactionCounterpartyRule.min_amount <= amount
                )
                amount_conditions.append(min_condition)

                # If max_amount is null or amount <= max_amount
                max_condition = or_(
                    TransactionCounterpartyRule.max_amount.is_(None), TransactionCounterpartyRule.max_amount >= amount
                )
                amount_conditions.append(max_condition)

                # Combine description and amount conditions
                rule_condition = and_(desc_condition, *amount_conditions)
                conditions.append(rule_condition)

            # Query for this batch
            if conditions:
                query = self.db_session.query(TransactionCounterpartyRule).filter(or_(*conditions))
                rules = query.all()

                # Map results back to descriptions
                for rule in rules:
                    # Find matching description from batch
                    for description, amount in batch:
                        if rule.normalized_description == description:
                            # Check amount range matches
                            min_ok = rule.min_amount is None or amount >= rule.min_amount
                            max_ok = rule.max_amount is None or amount <= rule.max_amount

                            if min_ok and max_ok:
                                result[description] = rule.counterparty_account_id
                                break  # Take first match per description

        return result
