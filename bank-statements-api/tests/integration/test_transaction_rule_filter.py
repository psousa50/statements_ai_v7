from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.enhancement_rule_pattern import EnhancementRulePattern
from app.domain.models.statement import Statement
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction


@pytest.fixture
def statement_for_user_a(db_session, account_for_user_a):
    statement = Statement(
        id=uuid4(),
        filename="test.csv",
        file_type="CSV",
        content=b"test",
        account_id=account_for_user_a.id,
    )
    db_session.add(statement)
    db_session.flush()
    return statement


def _create_transaction(db_session, account, statement, **overrides):
    defaults = dict(
        id=uuid4(),
        user_id=account.user_id,
        date=date(2023, 6, 15),
        description="Test Transaction",
        normalized_description="test transaction",
        amount=Decimal("-50.00"),
        account_id=account.id,
        statement_id=statement.id,
        source_type=SourceType.UPLOAD,
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        row_index=0,
        sort_index=0,
        exclude_from_analytics=False,
    )
    defaults.update(overrides)
    transaction = Transaction(**defaults)
    db_session.add(transaction)
    db_session.flush()
    return transaction


def _create_rule(db_session, user_id, patterns, **overrides):
    rule = EnhancementRule(
        id=uuid4(),
        source=EnhancementRuleSource.MANUAL,
        user_id=user_id,
        **overrides,
    )
    rule.patterns = [
        EnhancementRulePattern(normalized_description=desc, match_type=match_type, sort_order=i)
        for i, (desc, match_type) in enumerate(patterns)
    ]
    db_session.add(rule)
    db_session.flush()
    return rule


class TestTransactionRuleFilter:
    def test_exact_match_returns_only_matching_transactions(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        matching = _create_transaction(
            db_session, account_for_user_a, statement_for_user_a, normalized_description="vodafone dd"
        )
        _create_transaction(
            db_session, account_for_user_a, statement_for_user_a, normalized_description="other thing", sort_index=1
        )
        rule = _create_rule(db_session, user_a.id, [("vodafone dd", MatchType.EXACT)])

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, total_amount = repo.get_transactions_matching_rule_paginated(user_id=user_a.id, rule=rule)

        assert total == 1
        assert [t.id for t in transactions] == [matching.id]
        assert total_amount == Decimal("-50.00")

    def test_prefix_match(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        matching = _create_transaction(
            db_session, account_for_user_a, statement_for_user_a, normalized_description="amazon marketplace"
        )
        _create_transaction(
            db_session, account_for_user_a, statement_for_user_a, normalized_description="prime amazon", sort_index=1
        )
        rule = _create_rule(db_session, user_a.id, [("amazon", MatchType.PREFIX)])

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_transactions_matching_rule_paginated(user_id=user_a.id, rule=rule)

        assert total == 1
        assert [t.id for t in transactions] == [matching.id]

    def test_infix_match(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        matching = _create_transaction(
            db_session, account_for_user_a, statement_for_user_a, normalized_description="pay netflix sub"
        )
        _create_transaction(
            db_session, account_for_user_a, statement_for_user_a, normalized_description="spotify", sort_index=1
        )
        rule = _create_rule(db_session, user_a.id, [("netflix", MatchType.INFIX)])

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_transactions_matching_rule_paginated(user_id=user_a.id, rule=rule)

        assert total == 1
        assert [t.id for t in transactions] == [matching.id]

    def test_multiple_patterns_are_combined_with_or(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        first = _create_transaction(db_session, account_for_user_a, statement_for_user_a, normalized_description="vodafone dd")
        second = _create_transaction(
            db_session, account_for_user_a, statement_for_user_a, normalized_description="meo dd", sort_index=1
        )
        _create_transaction(db_session, account_for_user_a, statement_for_user_a, normalized_description="nos dd", sort_index=2)
        rule = _create_rule(
            db_session,
            user_a.id,
            [("vodafone dd", MatchType.EXACT), ("meo dd", MatchType.EXACT)],
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_transactions_matching_rule_paginated(user_id=user_a.id, rule=rule)

        assert total == 2
        assert {t.id for t in transactions} == {first.id, second.id}

    def test_amount_and_date_constraints_combine_with_pattern(
        self, db_session, user_a, account_for_user_a, statement_for_user_a
    ):
        matching = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            normalized_description="rent payment",
            amount=Decimal("-500.00"),
            date=date(2023, 6, 15),
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            normalized_description="rent payment",
            amount=Decimal("-10.00"),
            date=date(2023, 6, 15),
            sort_index=1,
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            normalized_description="rent payment",
            amount=Decimal("-500.00"),
            date=date(2022, 1, 1),
            sort_index=2,
        )
        rule = _create_rule(
            db_session,
            user_a.id,
            [("rent payment", MatchType.EXACT)],
            min_amount=Decimal("-600.00"),
            max_amount=Decimal("-100.00"),
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_transactions_matching_rule_paginated(user_id=user_a.id, rule=rule)

        assert total == 1
        assert [t.id for t in transactions] == [matching.id]

    def test_uncategorized_only_excludes_categorised_transactions(
        self, db_session, user_a, account_for_user_a, statement_for_user_a, category_for_user_a
    ):
        uncategorised = _create_transaction(
            db_session, account_for_user_a, statement_for_user_a, normalized_description="vodafone dd"
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            normalized_description="vodafone dd",
            category_id=category_for_user_a.id,
            categorization_status=CategorizationStatus.RULE_BASED,
            sort_index=1,
        )
        rule = _create_rule(db_session, user_a.id, [("vodafone dd", MatchType.EXACT)])

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_transactions_matching_rule_paginated(
            user_id=user_a.id, rule=rule, uncategorized_only=True
        )

        assert total == 1
        assert [t.id for t in transactions] == [uncategorised.id]

    def test_does_not_return_other_users_transactions(
        self, db_session, user_a, user_b, account_for_user_a, statement_for_user_a
    ):
        _create_transaction(db_session, account_for_user_a, statement_for_user_a, normalized_description="vodafone dd")
        rule = _create_rule(db_session, user_b.id, [("vodafone dd", MatchType.EXACT)])

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_transactions_matching_rule_paginated(user_id=user_b.id, rule=rule)

        assert total == 0
        assert transactions == []
