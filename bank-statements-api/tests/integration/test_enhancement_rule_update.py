from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.adapters.repositories.account import SQLAlchemyAccountRepository
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.enhancement_rule import SQLAlchemyEnhancementRuleRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.domain.models.enhancement_rule import MatchType
from app.domain.models.statement import Statement
from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus, SourceType, Transaction
from app.services.enhancement_rule_management import EnhancementRuleManagementService


@pytest.fixture
def service(db_session):
    return EnhancementRuleManagementService(
        enhancement_rule_repository=SQLAlchemyEnhancementRuleRepository(db_session),
        category_repository=SQLAlchemyCategoryRepository(db_session),
        account_repository=SQLAlchemyAccountRepository(db_session),
        transaction_repository=SQLAlchemyTransactionRepository(db_session),
        transaction_service=MagicMock(),
    )


def test_update_rule_keeping_unchanged_pattern_does_not_violate_unique_constraint(service, user_a, category_for_user_a):
    rule = service.create_rule(
        user_id=user_a.id,
        patterns=[{"normalized_description": "trf p fundo de pensoes", "match_type": MatchType.EXACT}],
    )

    updated = service.update_rule(
        rule_id=rule.id,
        user_id=user_a.id,
        patterns=[{"normalized_description": "trf p fundo de pensoes", "match_type": MatchType.EXACT}],
        category_id=category_for_user_a.id,
    )

    assert updated is not None
    assert updated.category_id == category_for_user_a.id
    assert [p.normalized_description for p in updated.patterns] == ["trf p fundo de pensoes"]


def test_update_rule_adds_and_removes_patterns(service, user_a):
    rule = service.create_rule(
        user_id=user_a.id,
        patterns=[
            {"normalized_description": "keep me", "match_type": MatchType.EXACT},
            {"normalized_description": "remove me", "match_type": MatchType.EXACT},
        ],
    )

    updated = service.update_rule(
        rule_id=rule.id,
        user_id=user_a.id,
        patterns=[
            {"normalized_description": "keep me", "match_type": MatchType.PREFIX},
            {"normalized_description": "add me", "match_type": MatchType.INFIX},
        ],
    )

    by_desc = {p.normalized_description: p for p in updated.patterns}
    assert set(by_desc) == {"keep me", "add me"}
    assert by_desc["keep me"].match_type == MatchType.PREFIX
    assert by_desc["add me"].match_type == MatchType.INFIX


def test_apply_to_existing_updates_matching_transactions_and_reports_count(
    service, db_session, user_a, account_for_user_a, category_for_user_a
):
    statement = Statement(id=uuid4(), filename="t.csv", file_type="CSV", content=b"x", account_id=account_for_user_a.id)
    db_session.add(statement)
    db_session.flush()

    transactions = []
    for i in range(3):
        transaction = Transaction(
            id=uuid4(),
            user_id=user_a.id,
            date=date(2024, 1, 1),
            description="Pocket EUR",
            normalized_description="pocket eur savings eur",
            amount=Decimal("-10.00"),
            account_id=account_for_user_a.id,
            statement_id=statement.id,
            source_type=SourceType.UPLOAD,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
            counterparty_status=CounterpartyStatus.UNPROCESSED,
            row_index=i,
            sort_index=i,
            exclude_from_analytics=False,
        )
        db_session.add(transaction)
        transactions.append(transaction)
    db_session.flush()

    rule = service.create_rule(
        user_id=user_a.id,
        patterns=[{"normalized_description": "pocket eur savings eur", "match_type": MatchType.EXACT}],
    )

    updated = service.update_rule(
        rule_id=rule.id,
        user_id=user_a.id,
        patterns=[{"normalized_description": "pocket eur savings eur", "match_type": MatchType.EXACT}],
        category_id=category_for_user_a.id,
        apply_to_existing=True,
    )

    assert updated.applied_transaction_count == 3
    for transaction in transactions:
        db_session.refresh(transaction)
        assert transaction.category_id == category_for_user_a.id
        assert transaction.categorization_status == CategorizationStatus.RULE_BASED


def test_apply_to_existing_skips_manually_categorized_transactions(
    service, db_session, user_a, account_for_user_a, category_for_user_a
):
    statement = Statement(id=uuid4(), filename="t.csv", file_type="CSV", content=b"x", account_id=account_for_user_a.id)
    db_session.add(statement)
    db_session.flush()

    manual = Transaction(
        id=uuid4(),
        user_id=user_a.id,
        date=date(2024, 1, 1),
        description="Pocket EUR",
        normalized_description="pocket eur savings eur",
        amount=Decimal("-10.00"),
        account_id=account_for_user_a.id,
        statement_id=statement.id,
        source_type=SourceType.UPLOAD,
        categorization_status=CategorizationStatus.MANUAL,
        counterparty_status=CounterpartyStatus.UNPROCESSED,
        row_index=0,
        sort_index=0,
        exclude_from_analytics=False,
    )
    db_session.add(manual)
    db_session.flush()

    rule = service.create_rule(
        user_id=user_a.id,
        patterns=[{"normalized_description": "pocket eur savings eur", "match_type": MatchType.EXACT}],
    )

    updated = service.update_rule(
        rule_id=rule.id,
        user_id=user_a.id,
        patterns=[{"normalized_description": "pocket eur savings eur", "match_type": MatchType.EXACT}],
        category_id=category_for_user_a.id,
        apply_to_existing=True,
    )

    assert updated.applied_transaction_count == 0
    db_session.refresh(manual)
    assert manual.category_id != category_for_user_a.id
    assert manual.categorization_status == CategorizationStatus.MANUAL
