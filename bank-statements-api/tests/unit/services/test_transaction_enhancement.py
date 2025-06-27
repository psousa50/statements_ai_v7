import uuid
from datetime import date
from decimal import Decimal

from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.services.transaction_enhancement import TransactionEnhancer


class TestTransactionEnhancer:
    def setup_method(self) -> None:
        self.enhancer = TransactionEnhancer()

    def create_transaction(
        self,
        normalized_description: str = "test transaction",
        amount: Decimal = Decimal("100.00"),
        transaction_date: date = date(2024, 1, 1),
        category_id: uuid.UUID = None,
        counterparty_account_id: uuid.UUID = None,
    ) -> Transaction:
        """Helper method to create test transactions"""
        transaction = Transaction()
        transaction.id = uuid.uuid4()
        transaction.normalized_description = normalized_description
        transaction.amount = amount
        transaction.date = transaction_date
        transaction.category_id = category_id
        transaction.counterparty_account_id = counterparty_account_id
        transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
        return transaction

    def create_rule(
        self,
        pattern: str = "test",
        match_type: MatchType = MatchType.EXACT,
        category_id: uuid.UUID = None,
        counterparty_account_id: uuid.UUID = None,
        min_amount: Decimal = None,
        max_amount: Decimal = None,
        start_date: date = None,
        end_date: date = None,
    ) -> EnhancementRule:
        """Helper method to create test enhancement rules"""
        rule = EnhancementRule()
        rule.id = uuid.uuid4()
        rule.normalized_description_pattern = pattern
        rule.match_type = match_type
        rule.category_id = category_id
        rule.counterparty_account_id = counterparty_account_id
        rule.min_amount = min_amount
        rule.max_amount = max_amount
        rule.start_date = start_date
        rule.end_date = end_date
        rule.source = EnhancementRuleSource.MANUAL
        return rule

    def test_apply_rules_empty_transactions(self):
        """Test that empty transaction list returns empty result"""
        rules = [self.create_rule()]
        result = self.enhancer.apply_rules([], rules)
        assert result == []

    def test_apply_rules_empty_rules(self):
        """Test that empty rules list leaves transactions unchanged"""
        transaction = self.create_transaction()
        original_category_id = transaction.category_id
        original_counterparty_id = transaction.counterparty_account_id

        result = self.enhancer.apply_rules([transaction], [])

        assert len(result) == 1
        assert result[0].category_id == original_category_id
        assert result[0].counterparty_account_id == original_counterparty_id

    def test_exact_match_rule_applies(self):
        """Test that exact match rule is applied correctly"""
        category_id = uuid.uuid4()
        counterparty_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="starbucks coffee")
        rule = self.create_rule(
            pattern="starbucks coffee",
            match_type=MatchType.EXACT,
            category_id=category_id,
            counterparty_account_id=counterparty_id,
        )

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id == category_id
        assert result[0].counterparty_account_id == counterparty_id
        assert result[0].categorization_status == CategorizationStatus.CATEGORIZED

    def test_exact_match_rule_does_not_apply_when_no_match(self):
        """Test that exact match rule doesn't apply when description doesn't match"""
        category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="starbucks coffee")
        rule = self.create_rule(pattern="dunkin donuts", match_type=MatchType.EXACT, category_id=category_id)

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id is None
        assert result[0].categorization_status == CategorizationStatus.UNCATEGORIZED

    def test_prefix_match_rule_applies(self):
        """Test that prefix match rule is applied correctly"""
        category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="mbway transfer to john")
        rule = self.create_rule(pattern="mbway", match_type=MatchType.PREFIX, category_id=category_id)

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id == category_id
        assert result[0].categorization_status == CategorizationStatus.CATEGORIZED

    def test_prefix_match_rule_does_not_apply_when_no_match(self):
        """Test that prefix match rule doesn't apply when description doesn't start with pattern"""
        category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="transfer via mbway")
        rule = self.create_rule(pattern="mbway", match_type=MatchType.PREFIX, category_id=category_id)

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id is None

    def test_infix_match_rule_applies(self):
        """Test that infix match rule is applied correctly"""
        category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="purchase at mercado lisboa")
        rule = self.create_rule(pattern="mercado", match_type=MatchType.INFIX, category_id=category_id)

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id == category_id
        assert result[0].categorization_status == CategorizationStatus.CATEGORIZED

    def test_infix_match_rule_does_not_apply_when_no_match(self):
        """Test that infix match rule doesn't apply when description doesn't contain pattern"""
        category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="purchase at supermarket")
        rule = self.create_rule(pattern="mercado", match_type=MatchType.INFIX, category_id=category_id)

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id is None

    def test_amount_constraints_respected(self):
        """Test that amount constraints are respected"""
        category_id = uuid.uuid4()

        # Transaction with amount 100
        transaction = self.create_transaction(normalized_description="test", amount=Decimal("100.00"))

        # Rule that only applies to amounts between 50 and 150
        rule = self.create_rule(
            pattern="test",
            match_type=MatchType.EXACT,
            category_id=category_id,
            min_amount=Decimal("50.00"),
            max_amount=Decimal("150.00"),
        )

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id == category_id

    def test_amount_constraints_prevent_match(self):
        """Test that amount constraints prevent rule application"""
        category_id = uuid.uuid4()

        # Transaction with amount 200
        transaction = self.create_transaction(normalized_description="test", amount=Decimal("200.00"))

        # Rule that only applies to amounts between 50 and 150
        rule = self.create_rule(
            pattern="test",
            match_type=MatchType.EXACT,
            category_id=category_id,
            min_amount=Decimal("50.00"),
            max_amount=Decimal("150.00"),
        )

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id is None

    def test_date_constraints_respected(self):
        """Test that date constraints are respected"""
        category_id = uuid.uuid4()

        # Transaction on 2024-06-15
        transaction = self.create_transaction(normalized_description="test", transaction_date=date(2024, 6, 15))

        # Rule that applies to dates between 2024-01-01 and 2024-12-31
        rule = self.create_rule(
            pattern="test",
            match_type=MatchType.EXACT,
            category_id=category_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id == category_id

    def test_date_constraints_prevent_match(self):
        """Test that date constraints prevent rule application"""
        category_id = uuid.uuid4()

        # Transaction on 2025-01-01
        transaction = self.create_transaction(normalized_description="test", transaction_date=date(2025, 1, 1))

        # Rule that applies to dates between 2024-01-01 and 2024-12-31
        rule = self.create_rule(
            pattern="test",
            match_type=MatchType.EXACT,
            category_id=category_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id is None

    def test_rule_precedence_exact_over_prefix(self):
        """Test that exact match rules take precedence over prefix match rules"""
        exact_category_id = uuid.uuid4()
        prefix_category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="starbucks coffee")

        # Prefix rule
        prefix_rule = self.create_rule(pattern="starbucks", match_type=MatchType.PREFIX, category_id=prefix_category_id)

        # Exact rule (should take precedence)
        exact_rule = self.create_rule(pattern="starbucks coffee", match_type=MatchType.EXACT, category_id=exact_category_id)

        result = self.enhancer.apply_rules([transaction], [prefix_rule, exact_rule])

        assert len(result) == 1
        assert result[0].category_id == exact_category_id

    def test_rule_precedence_prefix_over_infix(self):
        """Test that prefix match rules take precedence over infix match rules"""
        prefix_category_id = uuid.uuid4()
        infix_category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="starbucks coffee")

        # Infix rule
        infix_rule = self.create_rule(pattern="coffee", match_type=MatchType.INFIX, category_id=infix_category_id)

        # Prefix rule (should take precedence)
        prefix_rule = self.create_rule(pattern="starbucks", match_type=MatchType.PREFIX, category_id=prefix_category_id)

        result = self.enhancer.apply_rules([transaction], [infix_rule, prefix_rule])

        assert len(result) == 1
        assert result[0].category_id == prefix_category_id

    def test_only_first_matching_rule_applies(self):
        """Test that only the first matching rule is applied"""
        first_category_id = uuid.uuid4()
        second_category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="starbucks coffee")

        # Both rules match, but only first should apply
        first_rule = self.create_rule(pattern="starbucks", match_type=MatchType.PREFIX, category_id=first_category_id)

        second_rule = self.create_rule(pattern="coffee", match_type=MatchType.INFIX, category_id=second_category_id)

        result = self.enhancer.apply_rules([transaction], [first_rule, second_rule])

        assert len(result) == 1
        assert result[0].category_id == first_category_id

    def test_multiple_transactions_processed(self):
        """Test that multiple transactions are processed correctly"""
        category_id1 = uuid.uuid4()
        category_id2 = uuid.uuid4()

        transaction1 = self.create_transaction(normalized_description="starbucks coffee")
        transaction2 = self.create_transaction(normalized_description="walmart store")
        transaction3 = self.create_transaction(normalized_description="unknown merchant")

        rule1 = self.create_rule(pattern="starbucks", match_type=MatchType.PREFIX, category_id=category_id1)

        rule2 = self.create_rule(pattern="walmart", match_type=MatchType.PREFIX, category_id=category_id2)

        result = self.enhancer.apply_rules([transaction1, transaction2, transaction3], [rule1, rule2])

        assert len(result) == 3
        assert result[0].category_id == category_id1  # starbucks
        assert result[1].category_id == category_id2  # walmart
        assert result[2].category_id is None  # unknown merchant

    def test_category_only_rule_applies(self):
        """Test that rule with only category_id applies correctly"""
        category_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="test")
        rule = self.create_rule(
            pattern="test", match_type=MatchType.EXACT, category_id=category_id, counterparty_account_id=None
        )

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id == category_id
        assert result[0].counterparty_account_id is None
        assert result[0].categorization_status == CategorizationStatus.CATEGORIZED

    def test_counterparty_only_rule_applies(self):
        """Test that rule with only counterparty_account_id applies correctly"""
        counterparty_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="test")
        rule = self.create_rule(
            pattern="test", match_type=MatchType.EXACT, category_id=None, counterparty_account_id=counterparty_id
        )

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id is None
        assert result[0].counterparty_account_id == counterparty_id
        # Should not mark as categorized if only counterparty is set
        assert result[0].categorization_status == CategorizationStatus.UNCATEGORIZED

    def test_both_category_and_counterparty_rule_applies(self):
        """Test that rule with both category_id and counterparty_account_id applies correctly"""
        category_id = uuid.uuid4()
        counterparty_id = uuid.uuid4()

        transaction = self.create_transaction(normalized_description="test")
        rule = self.create_rule(
            pattern="test", match_type=MatchType.EXACT, category_id=category_id, counterparty_account_id=counterparty_id
        )

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id == category_id
        assert result[0].counterparty_account_id == counterparty_id
        assert result[0].categorization_status == CategorizationStatus.CATEGORIZED
