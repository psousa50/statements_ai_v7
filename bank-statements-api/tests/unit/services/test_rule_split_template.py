from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.enhancement_rule_pattern import EnhancementRulePattern
from app.domain.models.enhancement_rule_split_line import EnhancementRuleSplitLine
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService
from app.services.transaction_enhancement import TransactionEnhancer


def _make_transaction(**overrides):
    defaults = dict(
        id=uuid4(),
        date=date(2026, 5, 10),
        description="Vodafone DD",
        normalized_description="vodafone dd",
        amount=Decimal("60.00"),
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        sort_index=0,
        source_type=SourceType.UPLOAD,
        exclude_from_analytics=False,
        row_index=0,
        statement_id=uuid4(),
        account_id=uuid4(),
        user_id=uuid4(),
    )
    defaults.update(overrides)
    return Transaction(**defaults)


def _make_rule(split_lines):
    rule = EnhancementRule(
        id=uuid4(),
        user_id=uuid4(),
        source=EnhancementRuleSource.MANUAL,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    rule.patterns = [EnhancementRulePattern(normalized_description="vodafone dd", match_type=MatchType.EXACT, sort_order=0)]
    rule.split_lines = split_lines
    return rule


def _line(sort_order, amount=None, is_remainder=False, category_id=None, label=None):
    return EnhancementRuleSplitLine(
        id=uuid4(),
        rule_id=uuid4(),
        sort_order=sort_order,
        label=label,
        amount=Decimal(str(amount)) if amount is not None else None,
        is_remainder=is_remainder,
        category_id=category_id,
    )


@pytest.fixture
def service():
    return TransactionService(
        MagicMock(spec=TransactionRepository),
        MagicMock(spec=InitialBalanceRepository),
        MagicMock(spec=EnhancementRuleRepository),
        MagicMock(spec=TransactionEnhancer),
    )


class TestAutoSplitWithRule:
    def test_remainder_absorbs_balance(self, service):
        cat_internet, cat_sim, cat_support = uuid4(), uuid4(), uuid4()
        rule = _make_rule(
            [
                _line(0, amount="40.00", category_id=cat_internet, label="Internet"),
                _line(1, amount="15.00", category_id=cat_sim, label="SIM"),
                _line(2, is_remainder=True, category_id=cat_support, label="Support"),
            ]
        )
        parent = _make_transaction(amount=Decimal("-61.00"))
        service.transaction_repository.get_by_id.return_value = parent
        service.transaction_repository.split_transaction.return_value = []

        service.auto_split_with_rule(parent, rule)

        children = service.transaction_repository.split_transaction.call_args[0][1]
        amounts = {c.description: c.amount for c in children}
        assert amounts["Internet"] == Decimal("-40.00")
        assert amounts["SIM"] == Decimal("-15.00")
        assert amounts["Support"] == Decimal("-6.00")

    def test_skips_when_no_split_lines(self, service):
        rule = _make_rule([])
        parent = _make_transaction()
        result = service.auto_split_with_rule(parent, rule)
        assert result is None
        service.transaction_repository.split_transaction.assert_not_called()

    def test_skips_when_remainder_would_be_zero_or_negative(self, service):
        rule = _make_rule(
            [
                _line(0, amount="40.00", label="Internet"),
                _line(1, amount="30.00", label="SIM"),
                _line(2, is_remainder=True, label="Support"),
            ]
        )
        parent = _make_transaction(amount=Decimal("-60.00"))
        result = service.auto_split_with_rule(parent, rule)
        assert result is None
        service.transaction_repository.split_transaction.assert_not_called()

    def test_skips_child_transactions(self, service):
        rule = _make_rule(
            [
                _line(0, amount="40.00"),
                _line(1, is_remainder=True),
            ]
        )
        parent = _make_transaction(parent_transaction_id=uuid4())
        result = service.auto_split_with_rule(parent, rule)
        assert result is None

    def test_preserves_positive_sign_for_income(self, service):
        rule = _make_rule(
            [
                _line(0, amount="40.00", label="Internet"),
                _line(1, is_remainder=True, label="Rest"),
            ]
        )
        parent = _make_transaction(amount=Decimal("60.00"))
        service.transaction_repository.get_by_id.return_value = parent
        service.transaction_repository.split_transaction.return_value = []

        service.auto_split_with_rule(parent, rule)

        children = service.transaction_repository.split_transaction.call_args[0][1]
        amounts = {c.description: c.amount for c in children}
        assert amounts["Internet"] == Decimal("40.00")
        assert amounts["Rest"] == Decimal("20.00")
