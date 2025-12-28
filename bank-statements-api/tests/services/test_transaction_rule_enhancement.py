from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.transaction import CategorizationStatus
from app.services.transaction_rule_enhancement import EnhancementResult, TransactionRuleEnhancementService


class TestTransactionRuleEnhancementService:
    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_transaction_enhancer(self):
        return Mock()

    @pytest.fixture
    def mock_enhancement_rule_repository(self):
        return Mock()

    @pytest.fixture
    def enhancement_service(
        self,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
    ):
        return TransactionRuleEnhancementService(
            transaction_enhancer=mock_transaction_enhancer,
            enhancement_rule_repository=mock_enhancement_rule_repository,
        )

    @pytest.fixture
    def sample_dtos(self, user_id):
        return [
            TransactionDTO(
                date="2024-01-01",
                amount=100.0,
                description="Grocery Store Purchase",
                user_id=user_id,
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-02",
                amount=-50.0,
                description="ATM Withdrawal",
                user_id=user_id,
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-03",
                amount=200.0,
                description="Salary Payment",
                user_id=user_id,
                account_id="acc1",
            ),
        ]

    @pytest.fixture
    def sample_enhancement_rules(self):
        return [
            EnhancementRule(
                id=uuid4(),
                normalized_description_pattern="grocery store purchase",
                match_type=MatchType.EXACT,
                category_id="category-1",
                counterparty_account_id="counterparty-1",
                source=EnhancementRuleSource.MANUAL,
            ),
            EnhancementRule(
                id=uuid4(),
                normalized_description_pattern="salary",
                match_type=MatchType.PREFIX,
                category_id="category-2",
                counterparty_account_id=None,
                source=EnhancementRuleSource.AUTO,
            ),
        ]

    def test_enhance_transactions_empty_list(self, enhancement_service, user_id):
        result = enhancement_service.enhance_transactions(user_id, [])

        assert isinstance(result, EnhancementResult)
        assert result.enhanced_dtos == []
        assert result.total_processed == 0
        assert result.rule_based_matches == 0
        assert result.match_rate_percentage == 0.0
        assert not result.has_unmatched
        assert result.processing_time_ms >= 0

    def test_enhance_transactions_with_matches(
        self,
        enhancement_service,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
        sample_dtos,
        sample_enhancement_rules,
        user_id,
    ):
        mock_enhancement_rule_repository.find_matching_rules_batch.return_value = sample_enhancement_rules

        result = enhancement_service.enhance_transactions(user_id, sample_dtos)

        mock_enhancement_rule_repository.find_matching_rules_batch.assert_called_once()

        assert result.total_processed == 3
        assert result.rule_based_matches == 2
        assert result.match_rate_percentage == 66.7
        assert result.has_unmatched

        grocery_dto = next(dto for dto in result.enhanced_dtos if "grocery" in dto.description.lower())
        assert grocery_dto.category_id == "category-1"
        assert grocery_dto.categorization_status == CategorizationStatus.RULE_BASED
        assert grocery_dto.counterparty_account_id == "counterparty-1"
        assert grocery_dto.normalized_description == "grocery store purchase"

        salary_dto = next(dto for dto in result.enhanced_dtos if "salary" in dto.description.lower())
        assert salary_dto.category_id == "category-2"
        assert salary_dto.categorization_status == CategorizationStatus.RULE_BASED
        assert salary_dto.counterparty_account_id is None

        atm_dto = next(dto for dto in result.enhanced_dtos if "atm" in dto.description.lower())
        assert atm_dto.category_id is None
        assert atm_dto.categorization_status == CategorizationStatus.UNCATEGORIZED
        assert atm_dto.counterparty_account_id is None

    def test_enhance_transactions_no_matches(
        self,
        enhancement_service,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
        sample_dtos,
        user_id,
    ):
        mock_enhancement_rule_repository.find_matching_rules_batch.return_value = []

        result = enhancement_service.enhance_transactions(user_id, sample_dtos)

        assert result.total_processed == 3
        assert result.rule_based_matches == 0
        assert result.match_rate_percentage == 0.0
        assert result.has_unmatched

        for dto in result.enhanced_dtos:
            assert dto.category_id is None
            assert dto.categorization_status == CategorizationStatus.UNCATEGORIZED
            assert dto.counterparty_account_id is None
            assert dto.normalized_description is not None

    def test_enhance_transactions_creates_unmatched_rules(
        self,
        enhancement_service,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
        sample_dtos,
        user_id,
    ):
        mock_enhancement_rule_repository.find_matching_rules_batch.return_value = []
        mock_enhancement_rule_repository.find_by_normalized_description.return_value = None

        enhancement_service.enhance_transactions(user_id, sample_dtos)

        assert mock_enhancement_rule_repository.save.call_count == 3

        save_calls = mock_enhancement_rule_repository.save.call_args_list
        for call in save_calls:
            rule = call[0][0]
            assert isinstance(rule, EnhancementRule)
            assert rule.category_id is None
            assert rule.counterparty_account_id is None
            assert rule.source == EnhancementRuleSource.AUTO
            assert rule.match_type == MatchType.EXACT

    def test_enhance_transactions_handles_empty_descriptions(
        self,
        enhancement_service,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
        user_id,
    ):
        dtos = [
            TransactionDTO(
                date="2024-01-01",
                amount=100.0,
                description="",
                user_id=user_id,
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-02",
                amount=50.0,
                description="Valid Description",
                user_id=user_id,
                account_id="acc1",
            ),
        ]

        mock_enhancement_rule_repository.find_matching_rules_batch.return_value = []
        mock_enhancement_rule_repository.find_by_normalized_description.return_value = None

        result = enhancement_service.enhance_transactions(user_id, dtos)

        empty_dto = next(dto for dto in result.enhanced_dtos if not dto.description)
        assert empty_dto.categorization_status == CategorizationStatus.UNCATEGORIZED

        valid_dto = next(dto for dto in result.enhanced_dtos if dto.description == "Valid Description")
        assert valid_dto.normalized_description == "valid description"

        assert mock_enhancement_rule_repository.save.call_count == 1

    def test_enhancement_result_properties(self, user_id):
        dtos = [
            TransactionDTO(
                date="2024-01-01",
                amount=100.0,
                description="Test",
                user_id=user_id,
                account_id="acc1",
            )
        ]

        result = EnhancementResult(
            enhanced_dtos=dtos,
            total_processed=10,
            rule_based_matches=7,
            match_rate_percentage=70.0,
            processing_time_ms=150,
            has_unmatched=True,
        )

        assert result.enhanced_dtos == dtos
        assert result.total_processed == 10
        assert result.rule_based_matches == 7
        assert result.match_rate_percentage == 70.0
        assert result.processing_time_ms == 150
        assert result.has_unmatched is True

    def test_enhance_transactions_partial_matches(
        self,
        enhancement_service,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
        sample_dtos,
        sample_enhancement_rules,
        user_id,
    ):
        mock_enhancement_rule_repository.find_matching_rules_batch.return_value = sample_enhancement_rules
        mock_enhancement_rule_repository.find_by_normalized_description.return_value = None

        result = enhancement_service.enhance_transactions(user_id, sample_dtos)

        assert result.total_processed == 3
        assert result.rule_based_matches == 2
        assert result.match_rate_percentage == 66.7
        assert result.has_unmatched

        assert mock_enhancement_rule_repository.save.call_count == 1

    def test_enhance_transactions_creates_unique_rules_only(
        self,
        enhancement_service,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
        user_id,
    ):
        dtos = [
            TransactionDTO(
                date="2024-01-01",
                amount=100.0,
                description="Grocery Store Purchase",
                user_id=user_id,
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-02",
                amount=150.0,
                description="GROCERY STORE PURCHASE",
                user_id=user_id,
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-03",
                amount=75.0,
                description="grocery store purchase",
                user_id=user_id,
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-04",
                amount=50.0,
                description="ATM Withdrawal",
                user_id=user_id,
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-05",
                amount=25.0,
                description="atm withdrawal",
                user_id=user_id,
                account_id="acc1",
            ),
        ]

        mock_enhancement_rule_repository.find_matching_rules_batch.return_value = []
        mock_enhancement_rule_repository.find_by_normalized_description.return_value = None

        result = enhancement_service.enhance_transactions(user_id, dtos)

        assert mock_enhancement_rule_repository.save.call_count == 2

        save_calls = mock_enhancement_rule_repository.save.call_args_list
        created_patterns = {call[0][0].normalized_description_pattern for call in save_calls}
        expected_patterns = {
            "grocery store purchase",
            "atm withdrawal",
        }
        assert created_patterns == expected_patterns

        assert result.total_processed == 5
        assert result.rule_based_matches == 0
        assert result.has_unmatched
