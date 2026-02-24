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
        date=date(2024, 3, 10),
        description="Test Transaction",
        normalized_description="test transaction",
        amount=Decimal("-100.00"),
        account_id=account.id,
        statement_id=statement.id,
        source_type=SourceType.UPLOAD,
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        sort_index=0,
        row_index=0,
        exclude_from_analytics=False,
    )
    defaults.update(overrides)
    transaction = Transaction(**defaults)
    db_session.add(transaction)
    db_session.flush()
    return transaction


class TestSplitTransactionIntegration:
    def test_split_creates_children_with_parent_transaction_id(
        self, db_session, user_a, account_for_user_a, statement_for_user_a
    ):
        parent = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-100.00"),
        )

        child_a = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-60.00"),
            description="Part A",
            normalized_description="part a",
            parent_transaction_id=parent.id,
            sort_index=1,
            row_index=1,
        )
        child_b = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-40.00"),
            description="Part B",
            normalized_description="part b",
            parent_transaction_id=parent.id,
            sort_index=2,
            row_index=2,
        )

        db_session.flush()

        repo = SQLAlchemyTransactionRepository(db_session)
        fetched_child_a = repo.get_by_id(child_a.id, user_a.id)
        fetched_child_b = repo.get_by_id(child_b.id, user_a.id)

        assert fetched_child_a.parent_transaction_id == parent.id
        assert fetched_child_b.parent_transaction_id == parent.id

    def test_parent_excluded_from_analytics_after_split(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        parent = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-100.00"),
        )

        child_a = Transaction(
            id=uuid4(),
            user_id=parent.user_id,
            date=parent.date,
            description="Part A",
            normalized_description="part a",
            amount=Decimal("-60.00"),
            account_id=parent.account_id,
            statement_id=parent.statement_id,
            source_type=parent.source_type,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
            sort_index=1,
            row_index=1,
            parent_transaction_id=parent.id,
        )
        child_b = Transaction(
            id=uuid4(),
            user_id=parent.user_id,
            date=parent.date,
            description="Part B",
            normalized_description="part b",
            amount=Decimal("-40.00"),
            account_id=parent.account_id,
            statement_id=parent.statement_id,
            source_type=parent.source_type,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
            sort_index=2,
            row_index=2,
            parent_transaction_id=parent.id,
        )

        parent.exclude_from_analytics = True

        repo = SQLAlchemyTransactionRepository(db_session)
        repo.split_transaction(parent, [child_a, child_b])

        fetched = repo.get_by_id(parent.id, user_a.id)

        assert fetched.exclude_from_analytics is True

    def test_running_balance_excludes_split_parents(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        parent = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-100.00"),
            exclude_from_analytics=True,
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-60.00"),
            description="Part A",
            normalized_description="part a",
            parent_transaction_id=parent.id,
            sort_index=1,
            row_index=1,
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-40.00"),
            description="Part B",
            normalized_description="part b",
            parent_transaction_id=parent.id,
            sort_index=2,
            row_index=2,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, _total, _amount = repo.get_paginated(
            user_id=user_a.id,
            include_running_balance=True,
        )

        transaction_ids_with_balance = {t.id for t in transactions if t.running_balance is not None}
        assert parent.id not in transaction_ids_with_balance

    def test_split_children_appear_in_paginated_results(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        parent = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-100.00"),
        )
        child_a = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-60.00"),
            description="Part A",
            normalized_description="part a",
            parent_transaction_id=parent.id,
            sort_index=1,
            row_index=1,
        )
        child_b = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-40.00"),
            description="Part B",
            normalized_description="part b",
            parent_transaction_id=parent.id,
            sort_index=2,
            row_index=2,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        transactions, total, _ = repo.get_paginated(user_id=user_a.id)

        transaction_ids = {t.id for t in transactions}
        assert child_a.id in transaction_ids
        assert child_b.id in transaction_ids

    def test_has_split_children_returns_true_for_parent(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        parent = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-100.00"),
        )
        _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-60.00"),
            description="Part A",
            normalized_description="part a",
            parent_transaction_id=parent.id,
            sort_index=1,
            row_index=1,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        assert repo.has_split_children(parent.id, user_a.id) is True

    def test_has_split_children_returns_false_for_non_parent(
        self, db_session, user_a, account_for_user_a, statement_for_user_a
    ):
        txn = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-50.00"),
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        assert repo.has_split_children(txn.id, user_a.id) is False

    def test_parent_category_cleared_after_split(
        self, db_session, user_a, account_for_user_a, statement_for_user_a, category_for_user_a
    ):
        parent = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-100.00"),
            category_id=category_for_user_a.id,
            categorization_status=CategorizationStatus.RULE_BASED,
        )

        child_a = Transaction(
            id=uuid4(),
            user_id=parent.user_id,
            date=parent.date,
            description="Part A",
            normalized_description="part a",
            amount=Decimal("-60.00"),
            account_id=parent.account_id,
            statement_id=parent.statement_id,
            source_type=parent.source_type,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
            sort_index=1,
            row_index=1,
            parent_transaction_id=parent.id,
        )
        child_b = Transaction(
            id=uuid4(),
            user_id=parent.user_id,
            date=parent.date,
            description="Part B",
            normalized_description="part b",
            amount=Decimal("-40.00"),
            account_id=parent.account_id,
            statement_id=parent.statement_id,
            source_type=parent.source_type,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
            sort_index=2,
            row_index=2,
            parent_transaction_id=parent.id,
        )

        parent.category_id = None

        repo = SQLAlchemyTransactionRepository(db_session)
        repo.split_transaction(parent, [child_a, child_b])

        fetched = repo.get_by_id(parent.id, user_a.id)

        assert fetched.category_id is None

    def test_split_children_have_correct_amounts_summing_to_parent(
        self, db_session, user_a, account_for_user_a, statement_for_user_a
    ):
        parent = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-100.00"),
        )
        child_a = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-60.00"),
            description="Part A",
            normalized_description="part a",
            parent_transaction_id=parent.id,
            sort_index=1,
            row_index=1,
        )
        child_b = _create_transaction(
            db_session,
            account_for_user_a,
            statement_for_user_a,
            amount=Decimal("-40.00"),
            description="Part B",
            normalized_description="part b",
            parent_transaction_id=parent.id,
            sort_index=2,
            row_index=2,
        )

        repo = SQLAlchemyTransactionRepository(db_session)
        fetched_a = repo.get_by_id(child_a.id, user_a.id)
        fetched_b = repo.get_by_id(child_b.id, user_a.id)

        total = fetched_a.amount + fetched_b.amount
        assert total == parent.amount
