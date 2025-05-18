import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.adapters.categorizers.simple_transaction_categorizer import SimpleTransactionCategorizer
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
        transaction.description = "Test transaction"
        transaction.amount = 100.00

        # Execute
        result = self.categorizer.categorize(transaction)

        # Assert
        assert result == category_id
        self.category_repository.get_all.assert_called_once()

    def test_categorize_no_categories(self) -> None:
        # Setup
        self.category_repository.get_all.return_value = []

        transaction: Any = MagicMock()
        transaction.description = "Test transaction"
        transaction.amount = 100.00

        # Execute and Assert
        with pytest.raises(ValueError, match="No categories available for categorization"):
            self.categorizer.categorize(transaction)

        self.category_repository.get_all.assert_called_once()
