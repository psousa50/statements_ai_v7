from typing import Callable, Iterator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status

from app.api.schemas import BatchCategorizationResponse, CategorizationResponse, CategorizationResultResponse, TransactionCreate, TransactionListResponse, TransactionResponse, TransactionUpdate
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.transaction import CategorizationStatus


def register_transaction_routes(app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]):
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
    def create_transaction(
        transaction_data: TransactionCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        transaction = internal.transaction_service.create_transaction(
            transaction_date=transaction_data.date,
            description=transaction_data.description,
            amount=transaction_data.amount,
            category_id=transaction_data.category_id,
        )
        return transaction

    @router.get("", response_model=TransactionListResponse)
    def get_transactions(
        category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
        status: Optional[CategorizationStatus] = Query(None, description="Filter by categorization status"),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        transactions = internal.transaction_service.get_all_transactions()

        if category_id is not None:
            transactions = [t for t in transactions if t.category_id == category_id]

        if status is not None:
            transactions = [t for t in transactions if t.categorization_status == status]
        return TransactionListResponse(
            transactions=transactions,
            total=len(transactions),
        )

    @router.get("/{transaction_id}", response_model=TransactionResponse)
    def get_transaction(
        transaction_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        transaction = internal.transaction_service.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return transaction

    @router.put("/{transaction_id}", response_model=TransactionResponse)
    def update_transaction(
        transaction_id: UUID,
        transaction_data: TransactionUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        updated_transaction = internal.transaction_service.update_transaction(
            transaction_id=transaction_id,
            transaction_date=transaction_data.date,
            description=transaction_data.description,
            amount=transaction_data.amount,
            category_id=transaction_data.category_id,
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return updated_transaction

    @router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_transaction(
        transaction_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        deleted = internal.transaction_service.delete_transaction(transaction_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return None

    @router.put("/{transaction_id}/categorize", response_model=TransactionResponse)
    def categorize_transaction(
        transaction_id: UUID,
        category_id: Optional[UUID] = None,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        updated_transaction = internal.transaction_service.categorize_transaction(
            transaction_id=transaction_id,
            category_id=category_id,
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return updated_transaction

    @router.put("/{transaction_id}/mark-failure", response_model=TransactionResponse)
    def mark_categorization_failure(
        transaction_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        updated_transaction = internal.transaction_service.mark_categorization_failure(
            transaction_id=transaction_id,
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return updated_transaction

    @router.post("/categorize-batch", response_model=BatchCategorizationResponse)
    def categorize_transactions_batch(
        batch_size: int = Query(10, gt=0, le=100, description="Number of transactions to process"),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        try:
            batch_result = internal.transaction_categorization_service.process_uncategorized_transactions_detailed(batch_size=batch_size)
            
            # Convert domain results to API response format
            result_responses = [
                CategorizationResultResponse(
                    transaction_id=result.transaction_id,
                    category_id=result.category_id,
                    status=result.status,
                    error_message=result.error_message,
                    confidence=result.confidence
                )
                for result in batch_result.results
            ]
            
            return BatchCategorizationResponse(
                results=result_responses,
                total_processed=batch_result.total_processed,
                successful_count=batch_result.successful_count,
                failed_count=batch_result.failed_count,
                success=True,
                message=f"Processed {batch_result.total_processed} transactions: {batch_result.successful_count} categorized, {batch_result.failed_count} failed",
            )
        except Exception as e:
            return BatchCategorizationResponse(
                results=[],
                total_processed=0,
                successful_count=0,
                failed_count=0,
                success=False,
                message=f"Error categorizing transactions: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)
