import json
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock

from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.ai.llm_client import LLMClient
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.services.transaction_categorization.llm_transaction_categorizer import LLMCategorizationResult, LLMTransactionCategorizer


class MockLLMClient(LLMClient):
    """Mock LLM client for testing"""

    def __init__(self, fixed_response: str = ""):
        self.fixed_response = fixed_response
        self.last_prompt = None
        self.generate_called = False

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        self.generate_called = True
        return self.fixed_response

    async def generate_async(self, prompt: str) -> str:
        self.last_prompt = prompt
        self.generate_called = True
        return self.fixed_response


class TestLLMTransactionCategorizer:
    def setup_method(self) -> None:
        self.category_repository = MagicMock(spec=SQLAlchemyCategoryRepository)
        self.llm_client = MockLLMClient()

        # Create sample categories
        self.category1_id = uuid.uuid4()
        self.category2_id = uuid.uuid4()

        self.category1 = Mock()
        self.category1.id = self.category1_id
        self.category1.name = "Groceries"

        self.category2 = Mock()
        self.category2.id = self.category2_id
        self.category2.name = "Transportation"

        self.categories = [self.category1, self.category2]
        self.category_repository.get_all.return_value = self.categories

        self.categorizer = LLMTransactionCategorizer(categories_repository=self.category_repository, llm_client=self.llm_client)

    def test_init_loads_categories(self) -> None:
        """Test that initialization loads categories from repository"""
        # Assert
        self.category_repository.get_all.assert_called()
        assert self.categorizer.categories == self.categories

    def test_categorize_empty_transactions_returns_empty_list(self) -> None:
        """Test that categorizing empty transaction list returns empty results"""
        # Execute
        results = self.categorizer.categorize([])

        # Assert
        assert results == []
        assert not self.llm_client.generate_called

    def test_categorize_no_categories_returns_failure(self) -> None:
        """Test that categorizing with no categories returns failure results"""
        # Setup
        self.categorizer.categories = []
        transaction = self._create_sample_transaction()

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert result.error_message == "No categories available for categorization"
        assert not self.llm_client.generate_called

    def test_categorize_successful_llm_response(self) -> None:
        """Test successful categorization with valid LLM response"""
        # Setup
        transaction = self._create_sample_transaction()

        llm_response = json.dumps([{"transaction_description": transaction.description, "sub_category_id": str(self.category1_id), "confidence": 0.9}])

        self.llm_client.fixed_response = llm_response

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id == self.category1_id
        assert result.status == CategorizationStatus.CATEGORIZED
        assert result.confidence == 0.9
        assert result.error_message is None
        assert self.llm_client.generate_called

    def test_categorize_multiple_transactions_success(self) -> None:
        """Test successful categorization of multiple transactions"""
        # Setup
        transaction1 = self._create_sample_transaction(description="Grocery store purchase")
        transaction2 = self._create_sample_transaction(description="Bus ticket")

        llm_response = json.dumps(
            [
                {"transaction_description": transaction1.description, "sub_category_id": str(self.category1_id), "confidence": 0.85},
                {"transaction_description": transaction2.description, "sub_category_id": str(self.category2_id), "confidence": 0.75},
            ]
        )

        self.llm_client.fixed_response = llm_response

        # Execute
        results = self.categorizer.categorize([transaction1, transaction2])

        # Assert
        assert len(results) == 2

        # Check first result
        result1 = results[0]
        assert result1.transaction_id == transaction1.id
        assert result1.category_id == self.category1_id
        assert result1.status == CategorizationStatus.CATEGORIZED
        assert result1.confidence == 0.85

        # Check second result
        result2 = results[1]
        assert result2.transaction_id == transaction2.id
        assert result2.category_id == self.category2_id
        assert result2.status == CategorizationStatus.CATEGORIZED
        assert result2.confidence == 0.75

    def test_categorize_invalid_json_response(self) -> None:
        """Test handling of invalid JSON response from LLM"""
        # Setup
        transaction = self._create_sample_transaction()
        self.llm_client.fixed_response = "Invalid JSON response"

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert result.error_message == "Invalid JSON response from LLM"

    def test_categorize_empty_json_response(self) -> None:
        """Test handling of empty JSON response from LLM"""
        # Setup
        transaction = self._create_sample_transaction()
        self.llm_client.fixed_response = ""

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert result.error_message == "Invalid JSON response from LLM"

    def test_categorize_category_not_found(self) -> None:
        """Test handling when LLM returns category ID that doesn't exist"""
        # Setup
        transaction = self._create_sample_transaction()
        non_existent_category_id = uuid.uuid4()

        llm_response = json.dumps([{"transaction_description": transaction.description, "sub_category_id": str(non_existent_category_id), "confidence": 0.9}])

        self.llm_client.fixed_response = llm_response

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert f"Category with ID {non_existent_category_id} not found" in result.error_message

    def test_categorize_no_matching_transaction_from_llm(self) -> None:
        """Test handling when LLM response doesn't match any transaction"""
        # Setup
        transaction = self._create_sample_transaction()

        llm_response = json.dumps(
            [{"transaction_description": "Different transaction description", "sub_category_id": str(self.category1_id), "confidence": 0.9}]
        )

        self.llm_client.fixed_response = llm_response

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert result.error_message == "No matching result from LLM"

    def test_categorize_llm_client_without_generate_method(self) -> None:
        """Test fallback when LLM client doesn't have sync generate method"""
        # Setup
        mock_llm_client = Mock()
        # Remove the generate method to simulate async-only client
        if hasattr(mock_llm_client, "generate"):
            delattr(mock_llm_client, "generate")

        categorizer = LLMTransactionCategorizer(categories_repository=self.category_repository, llm_client=mock_llm_client)

        transaction = self._create_sample_transaction()

        # Execute
        results = categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id == self.category1_id  # Falls back to first category
        assert result.status == CategorizationStatus.CATEGORIZED
        assert result.confidence == 0.5
        assert result.error_message is None

    def test_categorize_llm_exception_handling(self) -> None:
        """Test handling of exceptions during LLM categorization"""
        # Setup
        transaction = self._create_sample_transaction()

        # Mock LLM client to raise an exception
        mock_llm_client = Mock()
        mock_llm_client.generate.side_effect = Exception("LLM service unavailable")

        categorizer = LLMTransactionCategorizer(categories_repository=self.category_repository, llm_client=mock_llm_client)

        # Execute
        results = categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert "LLM categorization error: LLM service unavailable" in result.error_message

    def test_categorize_partial_llm_response(self) -> None:
        """Test handling when LLM response has fewer results than transactions"""
        # Setup
        transaction1 = self._create_sample_transaction(description="First transaction")
        transaction2 = self._create_sample_transaction(description="Second transaction")

        # LLM response only has result for first transaction
        llm_response = json.dumps([{"transaction_description": transaction1.description, "sub_category_id": str(self.category1_id), "confidence": 0.8}])

        self.llm_client.fixed_response = llm_response

        # Execute
        results = self.categorizer.categorize([transaction1, transaction2])

        # Assert
        assert len(results) == 2

        # First transaction should be categorized
        result1 = results[0]
        assert result1.transaction_id == transaction1.id
        assert result1.category_id == self.category1_id
        assert result1.status == CategorizationStatus.CATEGORIZED

        # Second transaction should fail
        result2 = results[1]
        assert result2.transaction_id == transaction2.id
        assert result2.category_id is None
        assert result2.status == CategorizationStatus.FAILURE
        assert result2.error_message == "No matching result from LLM"

    def test_refresh_rules_updates_categories(self) -> None:
        """Test that refresh_rules updates categories from repository"""
        # Setup
        new_category = Mock()
        new_category.id = uuid.uuid4()
        new_category.name = "New Category"
        new_categories = [new_category]

        # Mock repository to return new categories on second call
        self.category_repository.get_all.return_value = new_categories

        # Execute
        result = self.categorizer.refresh_rules()

        # Assert
        assert result == new_categories
        assert self.categorizer.categories == new_categories
        # The call count might be higher due to setup - just verify refresh was called
        assert self.category_repository.get_all.call_count >= 2

    def test_llm_categorization_result_dataclass(self) -> None:
        """Test LLMCategorizationResult dataclass"""
        # Execute
        result = LLMCategorizationResult(transaction_description="Test transaction", sub_category_id=123, confidence=0.85)

        # Assert
        assert result.transaction_description == "Test transaction"
        assert result.sub_category_id == 123
        assert result.confidence == 0.85

    def test_categorize_with_uuid_as_int_in_response(self) -> None:
        """Test handling when LLM returns category ID as integer but should match UUID"""
        # Setup
        transaction = self._create_sample_transaction()

        # Convert UUID to int for the response (simulating LLM behavior)
        category_id_as_int = int(str(self.category1_id).replace("-", ""), 16) % (2**31)

        llm_response = json.dumps([{"transaction_description": transaction.description, "sub_category_id": category_id_as_int, "confidence": 0.9}])

        self.llm_client.fixed_response = llm_response

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result.transaction_id == transaction.id
        assert result.category_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert f"Category with ID {category_id_as_int} not found" in result.error_message

    def test_categorize_prompt_generation(self) -> None:
        """Test that categorization generates proper prompt for LLM"""
        # Setup
        transaction = self._create_sample_transaction()
        self.llm_client.fixed_response = json.dumps(
            [{"transaction_description": transaction.description, "sub_category_id": str(self.category1_id), "confidence": 0.9}]
        )

        # Execute
        self.categorizer.categorize([transaction])

        # Assert
        assert self.llm_client.last_prompt is not None
        assert transaction.description in self.llm_client.last_prompt
        assert "Available Categories" in self.llm_client.last_prompt

    def _create_sample_transaction(self, description: str = "Test transaction") -> Transaction:
        """Helper method to create a sample transaction"""
        transaction = Mock()
        transaction.id = uuid.uuid4()
        transaction.description = description
        transaction.amount = Decimal("100.50")
        transaction.date = date(2023, 4, 15)
        return transaction
