import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.domain.models.categorization import CategorizationResult
from app.domain.models.transaction import CategorizationStatus
from app.services.transaction_categorization.simple_transaction_categorizer import SimpleTransactionCategorizer
from app.ports.repositories.category import CategoryRepository


class TestSimpleTransactionCategorizer:
    def setup_method(self) -> None:
        self.category_repository: CategoryRepository = MagicMock(spec=CategoryRepository)
        self.categorizer = SimpleTransactionCategorizer(self.category_repository)

    def test_categorize_success(self) -> None:
        # Setup
        category_id = uuid.uuid4()
        category: Any = MagicMock()
        category.id = category_id
        category.name = "Test Category"
        self.category_repository.get_all.return_value = [category]

        transaction: Any = MagicMock()
        transaction.id = uuid.uuid4()
        transaction.description = "Test transaction"
        transaction.amount = 100.00

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, CategorizationResult)
        assert result.transaction_id == transaction.id
        assert result.category_id == category_id
        assert result.status == CategorizationStatus.CATEGORIZED
        assert result.confidence == 1.0
        self.category_repository.get_all.assert_called_once()

    def test_categorize_no_categories(self) -> None:
        # Setup
        self.category_repository.get_all.return_value = []

        transaction: Any = MagicMock()
        transaction.id = uuid.uuid4()
        transaction.description = "Test transaction"
        transaction.amount = 100.00

        # Execute
        results = self.categorizer.categorize([transaction])

        # Assert
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, CategorizationResult)
        assert result.transaction_id == transaction.id
        assert result.category_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert result.error_message == "No categories available for categorization"
        self.category_repository.get_all.assert_called_once()
