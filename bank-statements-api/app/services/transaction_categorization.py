from typing import List
from uuid import UUID

from app.domain.models.transaction import Transaction, CategorizationStatus
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
        
    def process_uncategorized_transactions(self, batch_size: int = 10) -> int:
        transactions: List[Transaction] = self.transaction_repository.get_oldest_uncategorized(limit=batch_size)
        
        if not transactions:
            return 0
            
        categorized_count: int = 0
        
        for transaction in transactions:
            try:
                category_id: UUID = self.transaction_categorizer.categorize(transaction)
                
                transaction.category_id = category_id
                transaction.categorization_status = CategorizationStatus.CATEGORIZED
                
                self.transaction_repository.update(transaction)
                
                categorized_count += 1
                
            except Exception:
                transaction.categorization_status = CategorizationStatus.FAILURE
                self.transaction_repository.update(transaction)
                
        return categorized_count
