from typing import List

from app.domain.models.enhancement_rule import EnhancementRule, MatchType
from app.domain.models.transaction import Transaction


class TransactionEnhancer:
    """
    Pure, stateless component for applying enhancement rules to transactions.

    This component applies a set of predefined enhancement rules to a list of transactions.
    It performs rule matching and enhancement logic only - it does not fetch rules,
    persist transactions, or manage execution order.
    """

    def apply_rules(
        self,
        transactions: List[Transaction],
        rules: List[EnhancementRule],
    ) -> List[Transaction]:
        """
        Apply enhancement rules to transactions.

        Rules are matched in precedence order:
        1. exact: description must exactly match the rule pattern
        2. prefix: transaction description must start with the rule pattern
        3. infix: description must contain the rule pattern

        Only the first matching rule per transaction is applied.

        Args:
            transactions: List of transactions to enhance
            rules: List of enhancement rules to apply

        Returns:
            List of enhanced transactions (same instances, modified in place)
        """
        # Sort rules by match type precedence
        sorted_rules = self._sort_rules_by_precedence(rules)

        for transaction in transactions:
            # Find first matching rule
            matching_rule = self._find_first_matching_rule(transaction, sorted_rules)

            if matching_rule:
                self._apply_rule_to_transaction(transaction, matching_rule)

        return transactions

    def _sort_rules_by_precedence(self, rules: List[EnhancementRule]) -> List[EnhancementRule]:
        """Sort rules by match type precedence: exact, prefix, infix"""
        precedence_order = {
            MatchType.EXACT: 1,
            MatchType.PREFIX: 2,
            MatchType.INFIX: 3,
        }

        return sorted(
            rules,
            key=lambda rule: precedence_order[rule.match_type],
        )

    def _find_first_matching_rule(
        self,
        transaction: Transaction,
        rules: List[EnhancementRule],
    ) -> EnhancementRule:
        """Find the first rule that matches the transaction"""
        for rule in rules:
            if rule.matches_transaction(transaction):
                return rule
        return None

    def _apply_rule_to_transaction(
        self,
        transaction: Transaction,
        rule: EnhancementRule,
    ):
        """Apply enhancement rule fields to the transaction"""
        if rule.category_id is not None:
            transaction.category_id = rule.category_id
            transaction.mark_rule_based_categorization()

        if rule.counterparty_account_id is not None:
            transaction.counterparty_account_id = rule.counterparty_account_id
            transaction.mark_rule_based_counterparty()
