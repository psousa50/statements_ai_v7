from uuid import UUID

from app.domain.models.transaction import Transaction
from app.ports.categorizers.transaction_categorizer import TransactionCategorizer
from app.ports.repositories.category import CategoryRepository


class SimpleTransactionCategorizer(TransactionCategorizer):
    def __init__(self, category_repository: CategoryRepository) -> None:
        self.category_repository: CategoryRepository = category_repository
        
    def categorize(self, transaction: Transaction) -> UUID:
        categories = self.category_repository.get_all()
        if not categories:
            raise ValueError("No categories available for categorization")
            
        return categories[0].id
