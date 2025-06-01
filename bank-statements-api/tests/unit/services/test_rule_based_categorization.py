import uuid
from typing import Dict, List
from unittest.mock import MagicMock, patch

from app.ports.repositories.transaction_categorization import (
    TransactionCategorizationRepository,
)
from app.services.rule_based_categorization import RuleBasedCategorizationService


class TestRuleBasedCategorizationService:
    def setup_method(self) -> None:
        self.repository = MagicMock(spec=TransactionCategorizationRepository)
        self.service = RuleBasedCategorizationService(self.repository)

    def test_categorize_batch_empty_list(self) -> None:
        """Test that empty input returns empty result"""
        result = self.service.categorize_batch([])

        assert result == {}
        self.repository.get_categories_by_normalized_descriptions.assert_not_called()

    def test_categorize_batch_no_matches(self) -> None:
        """Test when no descriptions match existing rules"""
        # Setup
        descriptions = ["unknown merchant", "new transaction"]
        self.repository.get_categories_by_normalized_descriptions.return_value = {}

        # Execute
        result = self.service.categorize_batch(descriptions)

        # Assert
        assert result == {}
        self.repository.get_categories_by_normalized_descriptions.assert_called_once_with(
            descriptions, batch_size=100
        )

    def test_categorize_batch_with_matches(self) -> None:
        """Test successful categorization with matches"""
        # Setup
        descriptions = ["starbucks coffee", "walmart store", "unknown merchant"]
        category_id_1 = uuid.uuid4()
        category_id_2 = uuid.uuid4()

        repository_result = {
            "starbucks coffee": category_id_1,
            "walmart store": category_id_2,
        }
        self.repository.get_categories_by_normalized_descriptions.return_value = (
            repository_result
        )

        # Execute
        result = self.service.categorize_batch(descriptions)

        # Assert
        expected = {
            "starbucks coffee": category_id_1,
            "walmart store": category_id_2,
        }
        assert result == expected
        self.repository.get_categories_by_normalized_descriptions.assert_called_once_with(
            descriptions, batch_size=100
        )

    def test_categorize_batch_custom_batch_size(self) -> None:
        """Test that custom batch size is passed to repository"""
        # Setup
        descriptions = ["test merchant"]
        custom_batch_size = 50
        self.repository.get_categories_by_normalized_descriptions.return_value = {}

        # Execute
        result = self.service.categorize_batch(
            descriptions, batch_size=custom_batch_size
        )

        # Assert
        assert result == {}
        self.repository.get_categories_by_normalized_descriptions.assert_called_once_with(
            descriptions, batch_size=custom_batch_size
        )

    def test_categorize_batch_handles_duplicates(self) -> None:
        """Test that duplicate descriptions are handled correctly"""
        # Setup
        descriptions = ["starbucks coffee", "starbucks coffee", "walmart store"]
        category_id_1 = uuid.uuid4()
        category_id_2 = uuid.uuid4()

        repository_result = {
            "starbucks coffee": category_id_1,
            "walmart store": category_id_2,
        }
        self.repository.get_categories_by_normalized_descriptions.return_value = (
            repository_result
        )

        # Execute
        result = self.service.categorize_batch(descriptions)

        # Assert
        expected = {
            "starbucks coffee": category_id_1,
            "walmart store": category_id_2,
        }
        assert result == expected
        # Repository should be called with original list (deduplication handled there)
        self.repository.get_categories_by_normalized_descriptions.assert_called_once_with(
            descriptions, batch_size=100
        )

    @patch("app.services.rule_based_categorization.logger")
    def test_categorize_batch_logs_statistics(self, mock_logger) -> None:
        """Test that categorization statistics are logged"""
        # Setup
        descriptions = ["starbucks coffee", "walmart store", "unknown merchant"]
        category_id = uuid.uuid4()

        repository_result = {
            "starbucks coffee": category_id,
        }
        self.repository.get_categories_by_normalized_descriptions.return_value = (
            repository_result
        )

        # Execute
        result = self.service.categorize_batch(descriptions)

        # Assert
        assert len(result) == 1
        # Verify logging was called with statistics
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args[0][0]
        assert "matched=1" in call_args
        assert "unmatched=2" in call_args
        assert "total=3" in call_args

    def test_categorize_batch_with_caching_enabled(self) -> None:
        """Test that caching works correctly when enabled"""
        # Setup
        descriptions = ["starbucks coffee", "walmart store"]
        category_id_1 = uuid.uuid4()
        category_id_2 = uuid.uuid4()

        repository_result = {
            "starbucks coffee": category_id_1,
            "walmart store": category_id_2,
        }
        self.repository.get_categories_by_normalized_descriptions.return_value = (
            repository_result
        )

        # Enable caching
        service_with_cache = RuleBasedCategorizationService(
            self.repository, enable_cache=True
        )

        # Execute first call
        result1 = service_with_cache.categorize_batch(descriptions)

        # Execute second call with same descriptions
        result2 = service_with_cache.categorize_batch(descriptions)

        # Assert
        assert result1 == result2
        assert result1 == repository_result
        # Repository should only be called once due to caching
        self.repository.get_categories_by_normalized_descriptions.assert_called_once()

    def test_categorize_batch_repository_exception_handling(self) -> None:
        """Test that repository exceptions are handled gracefully"""
        # Setup
        descriptions = ["test merchant"]
        self.repository.get_categories_by_normalized_descriptions.side_effect = (
            Exception("Database error")
        )

        # Execute & Assert
        try:
            result = self.service.categorize_batch(descriptions)
            # Should return empty dict on exception
            assert result == {}
        except Exception:
            # Should not propagate exceptions
            assert False, "Service should handle repository exceptions gracefully"

    @patch("app.services.rule_based_categorization.logger")
    def test_categorize_batch_logs_exceptions(self, mock_logger) -> None:
        """Test that exceptions are logged properly"""
        # Setup
        descriptions = ["test merchant"]
        error_message = "Database connection failed"
        self.repository.get_categories_by_normalized_descriptions.side_effect = (
            Exception(error_message)
        )

        # Execute
        result = self.service.categorize_batch(descriptions)

        # Assert
        assert result == {}
        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args[0][0]
        assert "Error in rule-based categorization" in call_args

    def test_get_cache_statistics(self) -> None:
        """Test cache statistics retrieval"""
        # Setup service with caching enabled
        service_with_cache = RuleBasedCategorizationService(
            self.repository, enable_cache=True
        )

        # Execute
        stats = service_with_cache.get_cache_statistics()

        # Assert
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "cache_size" in stats
        assert isinstance(stats["cache_hits"], int)
        assert isinstance(stats["cache_misses"], int)
        assert isinstance(stats["cache_size"], int)

    def test_clear_cache(self) -> None:
        """Test cache clearing functionality"""
        # Setup service with caching
        service_with_cache = RuleBasedCategorizationService(
            self.repository, enable_cache=True
        )

        # Add some data to cache
        descriptions = ["test merchant"]
        self.repository.get_categories_by_normalized_descriptions.return_value = {}
        service_with_cache.categorize_batch(descriptions)

        # Clear cache
        service_with_cache.clear_cache()

        # Execute same query again
        service_with_cache.categorize_batch(descriptions)

        # Assert repository was called twice (cache was cleared)
        assert self.repository.get_categories_by_normalized_descriptions.call_count == 2
