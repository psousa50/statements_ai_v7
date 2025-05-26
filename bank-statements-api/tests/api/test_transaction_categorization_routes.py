from unittest.mock import MagicMock
from uuid import uuid4

from app.api.schemas import BatchCategorizationResponse
from app.domain.models.categorization import BatchCategorizationResult, CategorizationResult
from app.domain.models.transaction import CategorizationStatus
from app.services.transaction_categorization.transaction_categorization import TransactionCategorizationService
from tests.api.helpers import build_client, mocked_dependencies


class TestTransactionCategorizationRoutes:
    def test_categorize_transactions_batch_success(self) -> None:
        # Create mock categorization results
        mock_results = [
            CategorizationResult(
                transaction_id=uuid4(),
                category_id=uuid4(),
                status=CategorizationStatus.CATEGORIZED
            ),
            CategorizationResult(
                transaction_id=uuid4(),
                category_id=uuid4(),
                status=CategorizationStatus.CATEGORIZED
            )
        ]
        mock_batch_result = BatchCategorizationResult(
            results=mock_results,
            total_processed=2,
            successful_count=2,
            failed_count=0
                )
        
        transaction_categorization_service = MagicMock(spec=TransactionCategorizationService)
        transaction_categorization_service.process_uncategorized_transactions_detailed.return_value = mock_batch_result
        client = build_client(internal_dependencies=mocked_dependencies(transaction_categorization_service=transaction_categorization_service))

        response = client.post("/api/v1/transactions/categorize-batch?batch_size=10")

        response = BatchCategorizationResponse.model_validate(response.json())

        assert response.total_processed == 2
        assert response.successful_count == 2
        assert response.failed_count == 0
        assert response.success
        assert response.message == "Processed 2 transactions: 2 categorized, 0 failed"
        assert len(response.results) == 2
        transaction_categorization_service.process_uncategorized_transactions_detailed.assert_called_once_with(batch_size=10)

    def test_categorize_transactions_batch_error(self) -> None:
        transaction_categorization_service = MagicMock(spec=TransactionCategorizationService)
        transaction_categorization_service.process_uncategorized_transactions_detailed.side_effect = ValueError("Test error")
        client = build_client(internal_dependencies=mocked_dependencies(transaction_categorization_service=transaction_categorization_service))

        response = client.post("/api/v1/transactions/categorize-batch?batch_size=10")

        response = BatchCategorizationResponse.model_validate(response.json())

        assert response.total_processed == 0
        assert response.successful_count == 0
        assert response.failed_count == 0
        assert not response.success
        assert response.message == "Error categorizing transactions: Test error"
        assert len(response.results) == 0
        transaction_categorization_service.process_uncategorized_transactions_detailed.assert_called_once_with(batch_size=10)
