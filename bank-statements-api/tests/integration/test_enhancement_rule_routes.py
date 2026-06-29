from unittest.mock import MagicMock

import pytest

from app.adapters.repositories.account import SQLAlchemyAccountRepository
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.enhancement_rule import SQLAlchemyEnhancementRuleRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.services.enhancement_rule_management import EnhancementRuleManagementService
from tests.api.helpers import build_client, mocked_dependencies


@pytest.fixture
def client(db_session, user_a):
    service = EnhancementRuleManagementService(
        enhancement_rule_repository=SQLAlchemyEnhancementRuleRepository(db_session),
        category_repository=SQLAlchemyCategoryRepository(db_session),
        account_repository=SQLAlchemyAccountRepository(db_session),
        transaction_repository=SQLAlchemyTransactionRepository(db_session),
        transaction_service=MagicMock(),
    )
    dependencies = mocked_dependencies(enhancement_rule_management_service=service)
    return build_client(internal_dependencies=dependencies, test_user=user_a)


def test_preview_endpoint_deserializes_patterns_and_returns_count(client):
    response = client.post(
        "/api/v1/enhancement-rules/preview/matching-transactions/count",
        json={"patterns": [{"normalized_description": "tfi jorge jesus costa", "match_type": "exact"}]},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_preview_endpoint_with_category_constraint(client, category_for_user_a):
    response = client.post(
        "/api/v1/enhancement-rules/preview/matching-transactions/count",
        json={
            "patterns": [{"normalized_description": "tfi jorge jesus costa", "match_type": "infix"}],
            "category_id": str(category_for_user_a.id),
            "min_amount": "10.00",
            "max_amount": "500.00",
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
