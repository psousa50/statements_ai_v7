from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.domain.models.account import Account
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


def _counterparty(db_session, user_id, name):
    account = Account(id=uuid4(), user_id=user_id, name=name, currency="EUR")
    db_session.add(account)
    db_session.flush()
    return account


def _create_transaction(db_session, account, statement, amount, counterparty=None, **overrides):
    defaults = dict(
        id=uuid4(),
        user_id=account.user_id,
        date=date(2023, 6, 15),
        description="Test Transaction",
        normalized_description="test transaction",
        amount=Decimal(amount),
        account_id=account.id,
        statement_id=statement.id,
        source_type=SourceType.UPLOAD,
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        counterparty_account_id=counterparty.id if counterparty else None,
        row_index=0,
        sort_index=0,
        exclude_from_analytics=False,
    )
    defaults.update(overrides)
    transaction = Transaction(**defaults)
    db_session.add(transaction)
    db_session.flush()
    return transaction


class TestCounterpartyTotals:
    def test_groups_by_counterparty_and_negates_amount(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        apt_1e = _counterparty(db_session, user_a.id, "1E")
        apt_1d = _counterparty(db_session, user_a.id, "1D")

        _create_transaction(db_session, account_for_user_a, statement_for_user_a, "100.00", apt_1e, sort_index=0)
        _create_transaction(db_session, account_for_user_a, statement_for_user_a, "50.00", apt_1e, sort_index=1)
        _create_transaction(db_session, account_for_user_a, statement_for_user_a, "30.00", apt_1d, sort_index=2)
        _create_transaction(db_session, account_for_user_a, statement_for_user_a, "-25.00", None, sort_index=3)

        repo = SQLAlchemyTransactionRepository(db_session)
        totals = repo.get_counterparty_totals(user_id=user_a.id)

        assert set(totals.keys()) == {apt_1e.id, apt_1d.id}
        assert totals[apt_1e.id]["total_amount"] == Decimal("-150.00")
        assert totals[apt_1e.id]["transaction_count"] == Decimal("2")
        assert totals[apt_1d.id]["total_amount"] == Decimal("-30.00")

    def test_transaction_type_filters_direction(self, db_session, user_a, account_for_user_a, statement_for_user_a):
        person = _counterparty(db_session, user_a.id, "Filipe")

        _create_transaction(db_session, account_for_user_a, statement_for_user_a, "200.00", person, sort_index=0)
        _create_transaction(db_session, account_for_user_a, statement_for_user_a, "-80.00", person, sort_index=1)

        repo = SQLAlchemyTransactionRepository(db_session)

        credit = repo.get_counterparty_totals(user_id=user_a.id, transaction_type="credit")
        assert credit[person.id]["total_amount"] == Decimal("-200.00")
        assert credit[person.id]["transaction_count"] == Decimal("1")

        debit = repo.get_counterparty_totals(user_id=user_a.id, transaction_type="debit")
        assert debit[person.id]["total_amount"] == Decimal("80.00")
