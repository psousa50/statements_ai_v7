import uuid
from typing import Any
from unittest.mock import MagicMock


from app.domain.models.transaction import CategorizationStatus
from app.ports.categorizers.transaction_categorizer import TransactionCategorizer
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction_categorization import TransactionCategorizationService


class TestTransactionCategorizationService:
    def setup_method(self) -> None:
        self.transaction_repository: TransactionRepository = MagicMock(spec=TransactionRepository)
        self.transaction_categorizer: TransactionCategorizer = MagicMock(spec=TransactionCategorizer)
        self.service = TransactionCategorizationService(
            transaction_repository=self.transaction_repository,
            transaction_categorizer=self.transaction_categorizer,
        )

    def test_process_uncategorized_transactions_empty(self) -> None:
        # Setup
        self.transaction_repository.get_oldest_uncategorized.return_value = []

        # Execute
        result = self.service.process_uncategorized_transactions(batch_size=10)

        # Assert
        assert result == 0
        self.transaction_repository.get_oldest_uncategorized.assert_called_once_with(limit=10)
        self.transaction_categorizer.categorize.assert_not_called()
        self.transaction_repository.update.assert_not_called()

    def test_process_uncategorized_transactions_success(self) -> None:
        # Setup
        category_id = uuid.uuid4()
        
        # Create mock transactions instead of real instances
        transaction1: Any = MagicMock()
        transaction1.categorization_status = CategorizationStatus.UNCATEGORIZED
        
        transaction2: Any = MagicMock()
        transaction2.categorization_status = CategorizationStatus.UNCATEGORIZED
        
        self.transaction_repository.get_oldest_uncategorized.return_value = [transaction1, transaction2]
        self.transaction_categorizer.categorize.return_value = category_id

        # Execute
        result = self.service.process_uncategorized_transactions(batch_size=10)

        # Assert
        assert result == 2
        self.transaction_repository.get_oldest_uncategorized.assert_called_once_with(limit=10)
        assert self.transaction_categorizer.categorize.call_count == 2
        assert self.transaction_repository.update.call_count == 2
        
        # Check that transactions were updated correctly
        assert transaction1.category_id == category_id
        assert transaction1.categorization_status == CategorizationStatus.CATEGORIZED
        assert transaction2.category_id == category_id
        assert transaction2.categorization_status == CategorizationStatus.CATEGORIZED

    def test_process_uncategorized_transactions_with_error(self) -> None:
        # Setup
        category_id = uuid.uuid4()
        
        # Create mock transactions instead of real instances
        transaction1: Any = MagicMock()
        transaction1.categorization_status = CategorizationStatus.UNCATEGORIZED
        
        transaction2: Any = MagicMock()
        transaction2.categorization_status = CategorizationStatus.UNCATEGORIZED
        transaction2.category_id = None
        
        self.transaction_repository.get_oldest_uncategorized.return_value = [transaction1, transaction2]
        
        # First call succeeds, second call raises an exception
        self.transaction_categorizer.categorize.side_effect = [
            category_id,
            ValueError("Categorization error")
        ]

        # Execute
        result = self.service.process_uncategorized_transactions(batch_size=10)

        # Assert
        assert result == 1
        self.transaction_repository.get_oldest_uncategorized.assert_called_once_with(limit=10)
        assert self.transaction_categorizer.categorize.call_count == 2
        assert self.transaction_repository.update.call_count == 2
        
        # Check that transactions were updated correctly
        assert transaction1.category_id == category_id
        assert transaction1.categorization_status == CategorizationStatus.CATEGORIZED
        assert transaction2.category_id is None
        assert transaction2.categorization_status == CategorizationStatus.FAILURE
