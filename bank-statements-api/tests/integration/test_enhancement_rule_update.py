from unittest.mock import MagicMock

import pytest

from app.adapters.repositories.account import SQLAlchemyAccountRepository
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.enhancement_rule import SQLAlchemyEnhancementRuleRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.domain.models.enhancement_rule import MatchType
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
