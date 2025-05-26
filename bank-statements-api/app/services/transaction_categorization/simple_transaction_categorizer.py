from typing import List

from app.domain.models.categorization import CategorizationResult
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.categorizers.transaction_categorizer import TransactionCategorizer
from app.ports.repositories.category import CategoryRepository


class SimpleTransactionCategorizer(TransactionCategorizer):
    def __init__(self, category_repository: CategoryRepository) -> None:
        self.category_repository: CategoryRepository = category_repository

    def categorize(self, transactions: List[Transaction]) -> List[CategorizationResult]:
        """Categorize a batch of transactions using the simple strategy"""
        categories = self.category_repository.get_all()
        if not categories:
            # Return failed results for all transactions
            return [
                CategorizationResult(
                    transaction_id=transaction.id,
                    category_id=None,
                    status=CategorizationStatus.FAILURE,
                    error_message="No categories available for categorization",
                )
                for transaction in transactions
            ]

        # Assign the first category to all transactions
        default_category_id = categories[0].id
        return [
            CategorizationResult(
                transaction_id=transaction.id,
                category_id=default_category_id,
                status=CategorizationStatus.CATEGORIZED,
                confidence=1.0,  # Simple categorizer is always "confident"
            )
            for transaction in transactions
        ]
