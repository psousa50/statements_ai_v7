from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.enhancement_rule import SQLAlchemyEnhancementRuleRepository
from app.adapters.repositories.initial_balance import SQLAlchemyInitialBalanceRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.domain.models.category import Category
from app.domain.models.statement import Statement
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.services.transaction import TransactionService
from app.services.transaction_enhancement import TransactionEnhancer


@pytest.fixture
def service(db_session):
    return TransactionService(
        SQLAlchemyTransactionRepository(db_session),
        SQLAlchemyInitialBalanceRepository(db_session),
        SQLAlchemyEnhancementRuleRepository(db_session),
        TransactionEnhancer(),
        SQLAlchemyCategoryRepository(db_session),
    )


@pytest.fixture
def root_with_child(db_session, user_a):
    root = Category(id=uuid4(), name="Housing", user_id=user_a.id)
    child = Category(id=uuid4(), name="Rent", user_id=user_a.id, parent_id=root.id)
    db_session.add_all([root, child])
    db_session.flush()
    return root, child


@pytest.fixture
def transaction_for_user_a(db_session, account_for_user_a):
    statement = Statement(
        id=uuid4(),
        filename="test.csv",
        file_type="CSV",
        content=b"test",
        account_id=account_for_user_a.id,
    )
    db_session.add(statement)
    db_session.flush()
    transaction = Transaction(
        id=uuid4(),
        user_id=account_for_user_a.user_id,
        date=date(2023, 6, 15),
        description="Test Transaction",
        normalized_description="test transaction",
        amount=Decimal("-50.00"),
        account_id=account_for_user_a.id,
        statement_id=statement.id,
        source_type=SourceType.UPLOAD,
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        row_index=0,
        sort_index=0,
    )
    db_session.add(transaction)
    db_session.flush()
    return transaction


def test_categorize_rejects_parent_category(service, user_a, root_with_child, transaction_for_user_a):
    root, _child = root_with_child

    with pytest.raises(ValueError, match="subcategories"):
        service.categorize_transaction(user_a.id, transaction_for_user_a.id, root.id)


def test_categorize_allows_leaf_category(service, user_a, root_with_child, transaction_for_user_a):
    _root, child = root_with_child

    result = service.categorize_transaction(user_a.id, transaction_for_user_a.id, child.id)

    assert result is not None
    assert result.category_id == child.id


def test_bulk_categorize_rejects_parent_category(service, user_a, root_with_child, transaction_for_user_a):
    root, _child = root_with_child

    with pytest.raises(ValueError, match="subcategories"):
        service.bulk_categorize_by_ids(user_a.id, [transaction_for_user_a.id], root.id)
