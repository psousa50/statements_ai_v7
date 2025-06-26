from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus
from app.services.transaction_rule_enhancement import EnhancementResult, TransactionRuleEnhancementService


class TestTransactionRuleEnhancementService:
    @pytest.fixture
    def mock_transaction_enhancer(self):
        return Mock()

    @pytest.fixture
    def mock_enhancement_rule_repository(self):
        return Mock()

    @pytest.fixture
    def enhancement_service(self, mock_transaction_enhancer, mock_enhancement_rule_repository):
        return TransactionRuleEnhancementService(
            transaction_enhancer=mock_transaction_enhancer,
            enhancement_rule_repository=mock_enhancement_rule_repository,
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
                source=EnhancementRuleSource.AI,
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
        self,
        enhancement_service,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
        sample_dtos,
        sample_enhancement_rules,
    ):
        """Test enhancement when rules match transactions"""
        # Setup mock responses
        mock_enhancement_rule_repository.get_all.return_value = sample_enhancement_rules

        # Mock enhanced transactions - first two match rules, third doesn't
        enhanced_transactions = []
        for i, dto in enumerate(sample_dtos):
            transaction = Mock()
            transaction.normalized_description = dto.description.lower()
            if i == 0:  # Grocery store matches
                transaction.category_id = "category-1"
                transaction.counterparty_account_id = "counterparty-1"
                transaction.categorization_status = CategorizationStatus.CATEGORIZED
                transaction.counterparty_status = CounterpartyStatus.INFERRED
            elif i == 1:  # ATM withdrawal doesn't match
                transaction.category_id = None
                transaction.counterparty_account_id = None
                transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
                transaction.counterparty_status = CounterpartyStatus.UNPROCESSED
            elif i == 2:  # Salary matches
                transaction.category_id = "category-2"
                transaction.counterparty_account_id = None
                transaction.categorization_status = CategorizationStatus.CATEGORIZED
                transaction.counterparty_status = CounterpartyStatus.UNPROCESSED
            enhanced_transactions.append(transaction)

        mock_transaction_enhancer.apply_rules.return_value = enhanced_transactions

        result = enhancement_service.enhance_transactions(sample_dtos)

        # Verify service calls
        mock_enhancement_rule_repository.get_all.assert_called_once()
        mock_transaction_enhancer.apply_rules.assert_called_once()

        # Verify transaction enhancer was called with correct arguments
        enhancer_args = mock_transaction_enhancer.apply_rules.call_args
        transactions_arg, rules_arg = enhancer_args[0]
        assert len(transactions_arg) == 3
        assert len(rules_arg) == 2

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
        self, enhancement_service, mock_transaction_enhancer, mock_enhancement_rule_repository, sample_dtos
    ):
        """Test enhancement when no rules match"""
        # Setup mock responses with no matches
        mock_enhancement_rule_repository.get_all.return_value = []

        # Mock enhanced transactions with no enhancements
        enhanced_transactions = []
        for dto in sample_dtos:
            transaction = Mock()
            transaction.normalized_description = dto.description.lower()
            transaction.category_id = None
            transaction.counterparty_account_id = None
            transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
            transaction.counterparty_status = CounterpartyStatus.UNPROCESSED
            enhanced_transactions.append(transaction)

        mock_transaction_enhancer.apply_rules.return_value = enhanced_transactions

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

    def test_enhance_transactions_creates_unmatched_rules(
        self, enhancement_service, mock_transaction_enhancer, mock_enhancement_rule_repository, sample_dtos
    ):
        """Test that unmatched transactions create enhancement rules"""
        # Setup mock responses with no matches
        mock_enhancement_rule_repository.get_all.return_value = []

        # Mock enhanced transactions with no enhancements
        enhanced_transactions = []
        for dto in sample_dtos:
            transaction = Mock()
            transaction.normalized_description = dto.description.lower()
            transaction.category_id = None
            transaction.counterparty_account_id = None
            transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
            transaction.counterparty_status = CounterpartyStatus.UNPROCESSED
            enhanced_transactions.append(transaction)

        mock_transaction_enhancer.apply_rules.return_value = enhanced_transactions

        enhancement_service.enhance_transactions(sample_dtos)

        # Verify unmatched rules were created
        assert mock_enhancement_rule_repository.save.call_count == 3  # One for each unmatched transaction

        # Verify rule creation calls
        save_calls = mock_enhancement_rule_repository.save.call_args_list
        for call in save_calls:
            rule = call[0][0]
            assert isinstance(rule, EnhancementRule)
            assert rule.category_id is None
            assert rule.counterparty_account_id is None
            assert rule.source == EnhancementRuleSource.AI
            assert rule.match_type == MatchType.EXACT

    def test_enhance_transactions_handles_empty_descriptions(
        self, enhancement_service, mock_transaction_enhancer, mock_enhancement_rule_repository
    ):
        """Test enhancement handles DTOs with empty descriptions gracefully"""
        # Create DTOs with empty and valid descriptions
        dtos = [
            TransactionDTO(date="2024-01-01", amount=100.0, description="", account_id="acc1"),  # Empty description
            TransactionDTO(date="2024-01-02", amount=50.0, description="Valid Description", account_id="acc1"),
        ]

        mock_enhancement_rule_repository.get_all.return_value = []

        # Mock enhanced transactions
        enhanced_transactions = []
        for dto in dtos:
            transaction = Mock()
            transaction.normalized_description = dto.description.lower() if dto.description else ""
            transaction.category_id = None
            transaction.counterparty_account_id = None
            transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
            transaction.counterparty_status = CounterpartyStatus.UNPROCESSED
            enhanced_transactions.append(transaction)

        mock_transaction_enhancer.apply_rules.return_value = enhanced_transactions

        result = enhancement_service.enhance_transactions(dtos)

        # Verify empty description DTO is handled correctly
        empty_dto = next(dto for dto in result.enhanced_dtos if not dto.description)
        assert empty_dto.categorization_status == CategorizationStatus.UNCATEGORIZED
        assert empty_dto.counterparty_status == CounterpartyStatus.UNPROCESSED

        # Verify valid description DTO was processed
        valid_dto = next(dto for dto in result.enhanced_dtos if dto.description == "Valid Description")
        assert valid_dto.normalized_description == "valid description"

        # Only one unmatched rule should be created (for the valid description)
        assert mock_enhancement_rule_repository.save.call_count == 1

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

    def test_enhance_transactions_partial_matches(
        self,
        enhancement_service,
        mock_transaction_enhancer,
        mock_enhancement_rule_repository,
        sample_dtos,
        sample_enhancement_rules,
    ):
        """Test enhancement with partial matches - some transactions enhanced, others not"""
        mock_enhancement_rule_repository.get_all.return_value = sample_enhancement_rules

        # Mock enhanced transactions - only first transaction matches
        enhanced_transactions = []
        for i, dto in enumerate(sample_dtos):
            transaction = Mock()
            transaction.normalized_description = dto.description.lower()
            if i == 0:  # Only grocery store matches
                transaction.category_id = "category-1"
                transaction.counterparty_account_id = "counterparty-1"
                transaction.categorization_status = CategorizationStatus.CATEGORIZED
                transaction.counterparty_status = CounterpartyStatus.INFERRED
            else:  # Others don't match
                transaction.category_id = None
                transaction.counterparty_account_id = None
                transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
                transaction.counterparty_status = CounterpartyStatus.UNPROCESSED
            enhanced_transactions.append(transaction)

        mock_transaction_enhancer.apply_rules.return_value = enhanced_transactions

        result = enhancement_service.enhance_transactions(sample_dtos)

        # Verify metrics
        assert result.total_processed == 3
        assert result.rule_based_matches == 1  # Only grocery store matched
        assert result.match_rate_percentage == 33.3
        assert result.has_unmatched  # Two transactions didn't match

        # Verify unmatched rules created for the 2 unmatched transactions
        assert mock_enhancement_rule_repository.save.call_count == 2

    def test_enhance_transactions_creates_unique_rules_only(
        self, enhancement_service, mock_transaction_enhancer, mock_enhancement_rule_repository
    ):
        """Test that only one rule is created per unique normalized description, even with duplicate transactions"""
        # Create multiple DTOs with duplicate normalized descriptions
        dtos = [
            TransactionDTO(date="2024-01-01", amount=100.0, description="Grocery Store Purchase", account_id="acc1"),
            TransactionDTO(date="2024-01-02", amount=150.0, description="GROCERY STORE PURCHASE", account_id="acc1"), # Same normalized
            TransactionDTO(date="2024-01-03", amount=75.0, description="grocery store purchase", account_id="acc1"),  # Same normalized
            TransactionDTO(date="2024-01-04", amount=50.0, description="ATM Withdrawal", account_id="acc1"),         # Different normalized
            TransactionDTO(date="2024-01-05", amount=25.0, description="atm withdrawal", account_id="acc1"),         # Same as above
        ]

        mock_enhancement_rule_repository.get_all.return_value = []

        # Mock enhanced transactions with no enhancements (all unmatched)
        enhanced_transactions = []
        for dto in dtos:
            transaction = Mock()
            transaction.normalized_description = dto.description.lower()
            transaction.category_id = None
            transaction.counterparty_account_id = None
            transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
            transaction.counterparty_status = CounterpartyStatus.UNPROCESSED
            enhanced_transactions.append(transaction)

        mock_transaction_enhancer.apply_rules.return_value = enhanced_transactions

        result = enhancement_service.enhance_transactions(dtos)

        # Verify only 2 unique rules were created (not 5)
        # "grocery store purchase" and "atm withdrawal"
        assert mock_enhancement_rule_repository.save.call_count == 2

        # Verify the unique normalized descriptions in the created rules
        save_calls = mock_enhancement_rule_repository.save.call_args_list
        created_patterns = {call[0][0].normalized_description_pattern for call in save_calls}
        expected_patterns = {"grocery store purchase", "atm withdrawal"}
        assert created_patterns == expected_patterns

        # Verify result metrics
        assert result.total_processed == 5
        assert result.rule_based_matches == 0  # No matches
        assert result.has_unmatched
