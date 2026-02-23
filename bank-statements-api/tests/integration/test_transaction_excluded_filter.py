from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
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
        sort_index=0,
        exclude_from_analytics=False,
    )
    defaults.update(overrides)
    transaction = Transaction(**defaults)
    db_session.add(transaction)
    db_session.flush()
    return transaction


class TestTransactionExcludedFilter:
    def test_filter_returns_only_excluded_transactions(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        _included = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Included Purchase",
            exclude_from_analytics=False,
        )
        excluded = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Excluded Purchase",
            exclude_from_analytics=True,
            sort_index=1,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_paginated(
            user_id=user_a.id,
            exclude_from_analytics=True,
        )

        assert total == 1
        assert len(transactions) == 1
        assert transactions[0].id == excluded.id
        assert transactions[0].exclude_from_analytics is True

    def test_filter_returns_only_included_transactions(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        included = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Included Purchase",
            exclude_from_analytics=False,
        )
        _excluded = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Excluded Purchase",
            exclude_from_analytics=True,
            sort_index=1,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_paginated(
            user_id=user_a.id,
            exclude_from_analytics=False,
        )

        assert total == 1
        assert len(transactions) == 1
        assert transactions[0].id == included.id
        assert transactions[0].exclude_from_analytics is False

    def test_no_filter_returns_all_transactions(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Included Purchase",
            exclude_from_analytics=False,
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Excluded Purchase",
            exclude_from_analytics=True,
            sort_index=1,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_paginated(user_id=user_a.id)

        assert total == 2
        assert len(transactions) == 2

    def test_excluded_filter_combines_with_date_range(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="January Excluded",
            date=date(2023, 1, 15),
            exclude_from_analytics=True,
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="June Excluded",
            date=date(2023, 6, 15),
            exclude_from_analytics=True,
            sort_index=1,
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="June Included",
            date=date(2023, 6, 20),
            exclude_from_analytics=False,
            sort_index=2,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_paginated(
            user_id=user_a.id,
            exclude_from_analytics=True,
            start_date=date(2023, 6, 1),
            end_date=date(2023, 6, 30),
        )

        assert total == 1
        assert transactions[0].description == "June Excluded"

    def test_excluded_filter_combines_with_category(
        self, db_session, user_a, account_for_user_a, statement_for_user_a, category_for_user_a
    ):
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Excluded with category",
            exclude_from_analytics=True,
            category_id=category_for_user_a.id,
            categorization_status=CategorizationStatus.RULE_BASED,
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Excluded without category",
            exclude_from_analytics=True,
            sort_index=1,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_paginated(
            user_id=user_a.id,
            exclude_from_analytics=True,
            category_ids=[category_for_user_a.id],
        )

        assert total == 1
        assert transactions[0].description == "Excluded with category"

    def test_excluded_filter_combines_with_amount_range(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Small excluded",
            amount=Decimal("-10.00"),
            exclude_from_analytics=True,
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Large excluded",
            amount=Decimal("-500.00"),
            exclude_from_analytics=True,
            sort_index=1,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_paginated(
            user_id=user_a.id,
            exclude_from_analytics=True,
            min_amount=Decimal("-600"),
            max_amount=Decimal("-100"),
        )

        assert total == 1
        assert transactions[0].description == "Large excluded"

    def test_empty_result_when_no_excluded_transactions_exist(
        self, db_session, user_a, account_for_user_a, statement_for_user_a
    ):
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            description="Included only",
            exclude_from_analytics=False,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_paginated(
            user_id=user_a.id,
            exclude_from_analytics=True,
        )

        assert total == 0
        assert len(transactions) == 0
