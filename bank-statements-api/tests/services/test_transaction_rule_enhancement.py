from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus
from app.services.transaction_rule_enhancement import EnhancementResult, TransactionRuleEnhancementService


class TestTransactionRuleEnhancementService:
    @pytest.fixture
    def mock_categorization_service(self):
        return Mock()

    @pytest.fixture
    def mock_counterparty_service(self):
        return Mock()

    @pytest.fixture
    def enhancement_service(self, mock_categorization_service, mock_counterparty_service):
        return TransactionRuleEnhancementService(
            rule_based_categorization_service=mock_categorization_service,
            rule_based_counterparty_service=mock_counterparty_service,
        )

    @pytest.fixture
    def sample_dtos(self):
        return [
            TransactionDTO(
                date="2024-01-01",
                amount=100.0,
                description="Grocery Store Purchase",
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-02",
                amount=-50.0,
                description="ATM Withdrawal",
                account_id="acc1",
            ),
            TransactionDTO(
                date="2024-01-03",
                amount=200.0,
                description="Salary Payment",
                account_id="acc1",
            ),
        ]

    def test_enhance_transactions_empty_list(self, enhancement_service):
        """Test enhancement with empty transaction list"""
        result = enhancement_service.enhance_transactions([])

        assert isinstance(result, EnhancementResult)
        assert result.enhanced_dtos == []
        assert result.total_processed == 0
        assert result.rule_based_matches == 0
        assert result.match_rate_percentage == 0.0
        assert not result.has_unmatched
        assert result.processing_time_ms >= 0

    def test_enhance_transactions_with_matches(
        self, enhancement_service, mock_categorization_service, mock_counterparty_service, sample_dtos
    ):
        """Test enhancement when rules match transactions"""
        # Setup mock responses
        mock_categorization_service.categorize_batch.return_value = {
            "grocery store purchase": "category-1",
            "salary payment": "category-2",
        }

        mock_counterparty_service.identify_counterparty_batch.return_value = {
            "grocery store purchase": "counterparty-1",
        }

        result = enhancement_service.enhance_transactions(sample_dtos)

        # Verify service calls
        mock_categorization_service.categorize_batch.assert_called_once()
        mock_counterparty_service.identify_counterparty_batch.assert_called_once()

        # Check categorization service was called with normalized descriptions
        categorization_args = mock_categorization_service.categorize_batch.call_args[0][0]
        assert len(categorization_args) == 3  # All unique descriptions
        assert "grocery store purchase" in categorization_args
        assert "atm withdrawal" in categorization_args
        assert "salary payment" in categorization_args

        # Check counterparty service was called with description-amount pairs
        counterparty_args = mock_counterparty_service.identify_counterparty_batch.call_args[0][0]
        assert len(counterparty_args) == 3
        assert ("grocery store purchase", Decimal("100.0")) in counterparty_args
        assert ("atm withdrawal", Decimal("-50.0")) in counterparty_args
        assert ("salary payment", Decimal("200.0")) in counterparty_args

        # Verify result
        assert result.total_processed == 3
        assert result.rule_based_matches == 2  # grocery store and salary matched
        assert result.match_rate_percentage == 66.7
        assert result.has_unmatched  # ATM withdrawal didn't match

        # Verify DTOs were enhanced
        grocery_dto = next(dto for dto in result.enhanced_dtos if "grocery" in dto.description.lower())
        assert grocery_dto.category_id == "category-1"
        assert grocery_dto.categorization_status == CategorizationStatus.CATEGORIZED
        assert grocery_dto.counterparty_account_id == "counterparty-1"
        assert grocery_dto.counterparty_status == CounterpartyStatus.INFERRED
        assert grocery_dto.normalized_description == "grocery store purchase"

        salary_dto = next(dto for dto in result.enhanced_dtos if "salary" in dto.description.lower())
        assert salary_dto.category_id == "category-2"
        assert salary_dto.categorization_status == CategorizationStatus.CATEGORIZED
        assert salary_dto.counterparty_account_id is None
        assert salary_dto.counterparty_status == CounterpartyStatus.UNPROCESSED

        atm_dto = next(dto for dto in result.enhanced_dtos if "atm" in dto.description.lower())
        assert atm_dto.category_id is None
        assert atm_dto.categorization_status == CategorizationStatus.UNCATEGORIZED
        assert atm_dto.counterparty_account_id is None
        assert atm_dto.counterparty_status == CounterpartyStatus.UNPROCESSED

    def test_enhance_transactions_no_matches(
        self, enhancement_service, mock_categorization_service, mock_counterparty_service, sample_dtos
    ):
        """Test enhancement when no rules match"""
        # Setup mock responses with no matches
        mock_categorization_service.categorize_batch.return_value = {}
        mock_counterparty_service.identify_counterparty_batch.return_value = {}

        result = enhancement_service.enhance_transactions(sample_dtos)

        # Verify result
        assert result.total_processed == 3
        assert result.rule_based_matches == 0
        assert result.match_rate_percentage == 0.0
        assert result.has_unmatched

        # Verify all DTOs are uncategorized
        for dto in result.enhanced_dtos:
            assert dto.category_id is None
            assert dto.categorization_status == CategorizationStatus.UNCATEGORIZED
            assert dto.counterparty_account_id is None
            assert dto.counterparty_status == CounterpartyStatus.UNPROCESSED
            assert dto.normalized_description is not None

    def test_enhance_transactions_with_duplicate_descriptions(
        self, enhancement_service, mock_categorization_service, mock_counterparty_service
    ):
        """Test enhancement deduplicates descriptions for efficiency"""
        dtos = [
            TransactionDTO(date="2024-01-01", amount=100.0, description="Grocery Store", account_id="acc1"),
            TransactionDTO(date="2024-01-02", amount=150.0, description="Grocery Store", account_id="acc1"),
            TransactionDTO(date="2024-01-03", amount=75.0, description="Gas Station", account_id="acc1"),
        ]

        mock_categorization_service.categorize_batch.return_value = {"grocery store": "category-1"}
        mock_counterparty_service.identify_counterparty_batch.return_value = {}

        result = enhancement_service.enhance_transactions(dtos)

        # Verify deduplication: should only call with unique descriptions
        categorization_args = mock_categorization_service.categorize_batch.call_args[0][0]
        assert len(categorization_args) == 2  # Only unique descriptions
        assert "grocery store" in categorization_args
        assert "gas station" in categorization_args

        # Verify both grocery transactions were enhanced
        grocery_dtos = [dto for dto in result.enhanced_dtos if "grocery" in dto.description.lower()]
        assert len(grocery_dtos) == 2
        for dto in grocery_dtos:
            assert dto.category_id == "category-1"
            assert dto.categorization_status == CategorizationStatus.CATEGORIZED

    def test_enhance_transactions_handles_empty_descriptions(
        self, enhancement_service, mock_categorization_service, mock_counterparty_service
    ):
        """Test enhancement handles DTOs with empty descriptions gracefully"""
        # Create DTOs with empty and valid descriptions
        dtos = [
            TransactionDTO(date="2024-01-01", amount=100.0, description="", account_id="acc1"),  # Empty description
            TransactionDTO(date="2024-01-02", amount=50.0, description="Valid Description", account_id="acc1"),
        ]

        # Setup mock responses - only the valid description should get results
        mock_categorization_service.categorize_batch.return_value = {"valid description": "category-1"}
        mock_counterparty_service.identify_counterparty_batch.return_value = {}

        result = enhancement_service.enhance_transactions(dtos)

        # Verify categorization was called with only non-empty normalized descriptions
        categorization_args = mock_categorization_service.categorize_batch.call_args[0][0]
        assert len(categorization_args) == 1
        assert "valid description" in categorization_args

        # Verify empty description DTO is handled correctly
        # The normalize_description function should convert empty string to an empty normalized string
        empty_dto = next(dto for dto in result.enhanced_dtos if not dto.description)
        assert empty_dto.categorization_status == CategorizationStatus.UNCATEGORIZED
        assert empty_dto.counterparty_status == CounterpartyStatus.UNPROCESSED

        # Verify valid description DTO was processed
        valid_dto = next(dto for dto in result.enhanced_dtos if dto.description == "Valid Description")
        assert valid_dto.category_id == "category-1"
        assert valid_dto.categorization_status == CategorizationStatus.CATEGORIZED

    def test_enhancement_result_properties(self):
        """Test EnhancementResult data class properties"""
        dtos = [TransactionDTO(date="2024-01-01", amount=100.0, description="Test", account_id="acc1")]

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
