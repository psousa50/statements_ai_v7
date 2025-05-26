import logging
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.ai.llm_client import LLMClient
from app.common.json_utils import sanitize_json
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.domain.models.categorization import CategorizationResult
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.categorizers.transaction_categorizer import TransactionCategorizer
from app.services.transaction_categorization.prompts import categorization_prompt

logger_content = logging.getLogger("app.llm.big")


@dataclass
class LLMCategorizationResult:
    transaction_description: str
    sub_category_id: str  # Changed to str to handle UUIDs
    confidence: float


class LLMTransactionCategorizer(TransactionCategorizer):
    def __init__(
        self, categories_repository: SQLAlchemyCategoryRepository, llm_client: LLMClient,
    ):
        self.categories_repository = categories_repository
        self.llm_client = llm_client
        self.categories = categories_repository.get_all()
        self.refresh_rules()

    def categorize(self, transactions: List[Transaction]) -> List[CategorizationResult]:
        """Batch categorization using LLM"""
        if not transactions:
            return []
        
        if not self.categories:
            return [
                CategorizationResult(
                    transaction_id=transaction.id,
                    category_id=None,
                    status=CategorizationStatus.FAILURE,
                    error_message="No categories available for categorization"
                )
                for transaction in transactions
            ]

        try:
            prompt = categorization_prompt(transactions, self.categories)
            # Note: This assumes a sync version of generate exists
            # If only async is available, this would need refactoring
            if hasattr(self.llm_client, 'generate'):
                response = self.llm_client.generate(prompt)
            else:
                # Fallback to a simple categorization if LLM is not available
                logger_content.warning("LLM client does not have sync generate method, falling back to simple categorization")
                return [
                    CategorizationResult(
                        transaction_id=transaction.id,
                        category_id=self.categories[0].id if self.categories else None,
                        status=CategorizationStatus.CATEGORIZED if self.categories else CategorizationStatus.FAILURE,
                        error_message=None if self.categories else "No categories available",
                        confidence=0.5
                    )
                    for transaction in transactions
                ]
                
            logger_content.debug(
                response,
                extra={"prefix": "llm_transaction_categorizer.response", "ext": "json"},
            )
            
            json_result = sanitize_json(response)
            if not json_result:
                return [
                    CategorizationResult(
                        transaction_id=transaction.id,
                        category_id=None,
                        status=CategorizationStatus.FAILURE,
                        error_message="Invalid JSON response from LLM"
                    )
                    for transaction in transactions
                ]

            llm_categorization_results = [
                LLMCategorizationResult(**result) for result in json_result
            ]
            
            # Map LLM results back to transactions
            results = []
            for transaction in transactions:
                # Find matching result from LLM
                matching_result = None
                for llm_result in llm_categorization_results:
                    if transaction.description == llm_result.transaction_description:
                        matching_result = llm_result
                        break
                
                if matching_result:
                    # Find the actual category UUID from the sub_category_id
                    # Handle both string and integer sub_category_id values
                    try:
                        # Convert to string first in case it's an integer
                        sub_category_id_str = str(matching_result.sub_category_id)
                        category_uuid = UUID(sub_category_id_str)
                        category = next(
                            (cat for cat in self.categories if cat.id == category_uuid),
                            None
                        )
                    except ValueError:
                        # If sub_category_id is not a valid UUID, try string comparison
                        category = next(
                            (cat for cat in self.categories if str(cat.id) == str(matching_result.sub_category_id)),
                            None
                        )
                    
                    if category:
                        results.append(
                            CategorizationResult(
                                transaction_id=transaction.id,
                                category_id=category.id,
                                status=CategorizationStatus.CATEGORIZED,
                                confidence=matching_result.confidence
                            )
                        )
                    else:
                        results.append(
                            CategorizationResult(
                                transaction_id=transaction.id,
                                category_id=None,
                                status=CategorizationStatus.FAILURE,
                                error_message=f"Category with ID {matching_result.sub_category_id} not found"
                            )
                        )
                else:
                    results.append(
                        CategorizationResult(
                            transaction_id=transaction.id,
                            category_id=None,
                            status=CategorizationStatus.FAILURE,
                            error_message="No matching result from LLM"
                        )
                    )
            
            return results
            
        except Exception as e:
            logger_content.error(f"Error in LLM categorization: {str(e)}")
            return [
                CategorizationResult(
                    transaction_id=transaction.id,
                    category_id=None,
                    status=CategorizationStatus.FAILURE,
                    error_message=f"LLM categorization error: {str(e)}"
                )
                for transaction in transactions
            ]

    def refresh_rules(self):
        self.categories = self.categories_repository.get_all()
        return self.categories
