from unittest.mock import MagicMock

import pytest

from app.api.schemas import EnhancementRulePatternInput, EnhancementRulePreview
from app.domain.models.enhancement_rule import MatchType
from app.services.enhancement_rule_management import EnhancementRuleManagementService


@pytest.fixture
def service():
    transaction_repository = MagicMock()
    transaction_repository.count_matching_rule.return_value = 7

    return (
        EnhancementRuleManagementService(
            enhancement_rule_repository=MagicMock(),
            category_repository=MagicMock(),
            account_repository=MagicMock(),
            transaction_repository=transaction_repository,
            transaction_service=MagicMock(),
        ),
        transaction_repository,
    )


def test_preview_accepts_pydantic_pattern_inputs(service):
    rule_service, transaction_repository = service

    preview = EnhancementRulePreview(
        patterns=[EnhancementRulePatternInput(normalized_description="tfi jorge jesus costa", match_type=MatchType.EXACT)],
    )

    result = rule_service.preview_matching_transactions_count(preview, user_id=None)

    assert result["count"] == 7
    temp_rule = transaction_repository.count_matching_rule.call_args[0][0]
    assert [p.normalized_description for p in temp_rule.patterns] == ["tfi jorge jesus costa"]
    assert temp_rule.patterns[0].match_type == MatchType.EXACT
