from typing import List

from app.domain.models.categorization import BatchCategorizationResult, CategorizationResult
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.categorizers.transaction_categorizer import TransactionCategorizer
from app.ports.repositories.transaction import TransactionRepository


class TransactionCategorizationService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        transaction_categorizer: TransactionCategorizer,
    ) -> None:
        self.transaction_repository: TransactionRepository = transaction_repository
        self.transaction_categorizer: TransactionCategorizer = transaction_categorizer

    def process_uncategorized_transactions_detailed(self, batch_size: int = 10) -> BatchCategorizationResult:
        transactions: List[Transaction] = self.transaction_repository.get_oldest_uncategorized(limit=batch_size)

        if not transactions:
            return BatchCategorizationResult(results=[], total_processed=0, successful_count=0, failed_count=0)

        categorization_results: List[CategorizationResult] = self.transaction_categorizer.categorize(transactions)

        for result in categorization_results:
            transaction = next((t for t in transactions if t.id == result.transaction_id), None)
            if transaction:
                transaction.category_id = result.category_id
                transaction.categorization_status = result.status
                self.transaction_repository.update(transaction)

        successful_count = sum(1 for result in categorization_results if result.status == CategorizationStatus.CATEGORIZED)
        failed_count = len(categorization_results) - successful_count

        return BatchCategorizationResult(
            results=categorization_results,
            total_processed=len(categorization_results),
            successful_count=successful_count,
            failed_count=failed_count,
        )
