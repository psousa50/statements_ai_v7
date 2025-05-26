import uuid
from typing import Any
from unittest.mock import MagicMock

from app.domain.models.categorization import BatchCategorizationResult, CategorizationResult
from app.domain.models.transaction import CategorizationStatus
from app.ports.categorizers.transaction_categorizer import TransactionCategorizer
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction_categorization.transaction_categorization import TransactionCategorizationService


class TestTransactionCategorizationService:
    def setup_method(self) -> None:
        self.transaction_repository: TransactionRepository = MagicMock(spec=TransactionRepository)
        self.transaction_categorizer: TransactionCategorizer = MagicMock(spec=TransactionCategorizer)
        self.service = TransactionCategorizationService(
            transaction_repository=self.transaction_repository,
            transaction_categorizer=self.transaction_categorizer,
        )

    def test_process_uncategorized_transactions_detailed_empty(self) -> None:
        # Setup
        self.transaction_repository.get_oldest_uncategorized.return_value = []

        # Execute
        result = self.service.process_uncategorized_transactions_detailed(batch_size=10)

        # Assert
        assert isinstance(result, BatchCategorizationResult)
        assert result.total_processed == 0
        assert result.successful_count == 0
        assert result.failed_count == 0
        assert len(result.results) == 0
        self.transaction_repository.get_oldest_uncategorized.assert_called_once_with(limit=10)
        self.transaction_categorizer.categorize.assert_not_called()
        self.transaction_repository.update.assert_not_called()

    def test_process_uncategorized_transactions_detailed_success(self) -> None:
        # Setup
        category_id = uuid.uuid4()
        transaction_id1 = uuid.uuid4()
        transaction_id2 = uuid.uuid4()

        # Create mock transactions
        transaction1: Any = MagicMock()
        transaction1.id = transaction_id1
        transaction1.categorization_status = CategorizationStatus.UNCATEGORIZED

        transaction2: Any = MagicMock()
        transaction2.id = transaction_id2
        transaction2.categorization_status = CategorizationStatus.UNCATEGORIZED

        self.transaction_repository.get_oldest_uncategorized.return_value = [transaction1, transaction2]

        # Mock the batch categorizer to return successful results
        mock_categorization_results = [
            CategorizationResult(transaction_id=transaction_id1, category_id=category_id, status=CategorizationStatus.CATEGORIZED),
            CategorizationResult(transaction_id=transaction_id2, category_id=category_id, status=CategorizationStatus.CATEGORIZED),
        ]
        self.transaction_categorizer.categorize.return_value = mock_categorization_results

        # Execute
        result = self.service.process_uncategorized_transactions_detailed(batch_size=10)

        # Assert
        assert isinstance(result, BatchCategorizationResult)
        assert result.total_processed == 2
        assert result.successful_count == 2
        assert result.failed_count == 0
        assert len(result.results) == 2
        self.transaction_repository.get_oldest_uncategorized.assert_called_once_with(limit=10)
        self.transaction_categorizer.categorize.assert_called_once_with([transaction1, transaction2])
        assert self.transaction_repository.update.call_count == 2

        # Check that transactions were updated correctly
        assert transaction1.category_id == category_id
        assert transaction1.categorization_status == CategorizationStatus.CATEGORIZED
        assert transaction2.category_id == category_id
        assert transaction2.categorization_status == CategorizationStatus.CATEGORIZED

    def test_process_uncategorized_transactions_detailed_with_failures(self) -> None:
        # Setup
        category_id = uuid.uuid4()
        transaction_id1 = uuid.uuid4()
        transaction_id2 = uuid.uuid4()

        # Create mock transactions
        transaction1: Any = MagicMock()
        transaction1.id = transaction_id1
        transaction1.categorization_status = CategorizationStatus.UNCATEGORIZED

        transaction2: Any = MagicMock()
        transaction2.id = transaction_id2
        transaction2.categorization_status = CategorizationStatus.UNCATEGORIZED

        self.transaction_repository.get_oldest_uncategorized.return_value = [transaction1, transaction2]

        # Mock the batch categorizer to return mixed results (one success, one failure)
        mock_categorization_results = [
            CategorizationResult(transaction_id=transaction_id1, category_id=category_id, status=CategorizationStatus.CATEGORIZED),
            CategorizationResult(transaction_id=transaction_id2, category_id=None, status=CategorizationStatus.FAILURE, error_message="Categorization failed"),
        ]
        self.transaction_categorizer.categorize.return_value = mock_categorization_results

        # Execute
        result = self.service.process_uncategorized_transactions_detailed(batch_size=10)

        # Assert
        assert isinstance(result, BatchCategorizationResult)
        assert result.total_processed == 2
        assert result.successful_count == 1
        assert result.failed_count == 1
        assert len(result.results) == 2
        self.transaction_repository.get_oldest_uncategorized.assert_called_once_with(limit=10)
        self.transaction_categorizer.categorize.assert_called_once_with([transaction1, transaction2])
        assert self.transaction_repository.update.call_count == 2

        # Check that transactions were updated correctly
        assert transaction1.category_id == category_id
        assert transaction1.categorization_status == CategorizationStatus.CATEGORIZED
        assert transaction2.category_id is None
        assert transaction2.categorization_status == CategorizationStatus.FAILURE
