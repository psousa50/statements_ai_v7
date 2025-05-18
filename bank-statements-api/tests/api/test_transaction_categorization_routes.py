from unittest.mock import MagicMock

from tests.api.helpers import build_client, mocked_dependencies
from app.api.schemas import CategorizationResponse
from app.services.transaction_categorization import TransactionCategorizationService


class TestTransactionCategorizationRoutes:
    def test_categorize_transactions_batch_success(self) -> None:
        transaction_categorization_service = MagicMock(spec=TransactionCategorizationService)
        transaction_categorization_service.process_uncategorized_transactions.return_value = 5
        client = build_client(internal_dependencies=mocked_dependencies(transaction_categorization_service=transaction_categorization_service))

        response = client.post("/api/v1/transactions/categorize-batch?batch_size=10")

        response = CategorizationResponse.model_validate(response.json())

        assert response.categorized_count == 5
        assert response.success == True
        assert response.message == "Successfully categorized 5 transactions"
        transaction_categorization_service.process_uncategorized_transactions.assert_called_once_with(batch_size=10)

    def test_categorize_transactions_batch_error(self) -> None:
        transaction_categorization_service = MagicMock(spec=TransactionCategorizationService)
        transaction_categorization_service.process_uncategorized_transactions.side_effect = ValueError("Test error")
        client = build_client(internal_dependencies=mocked_dependencies(transaction_categorization_service=transaction_categorization_service))

        response = client.post("/api/v1/transactions/categorize-batch?batch_size=10")

        response = CategorizationResponse.model_validate(response.json())

        assert response.categorized_count == 0
        assert response.success == False
        assert response.message == "Error categorizing transactions: Test error"
        transaction_categorization_service.process_uncategorized_transactions.assert_called_once_with(batch_size=10)
