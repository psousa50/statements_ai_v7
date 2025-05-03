from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, FastAPI, HTTPException, Query, status

from app.api.schemas import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.core.dependencies import InternalDependencies
from app.domain.models.transaction import CategorizationStatus


def register_transaction_routes(app: FastAPI, internal: InternalDependencies):
    """Register transaction routes with the FastAPI app."""
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.post(
        "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
    )
    def create_transaction(transaction_data: TransactionCreate):
        """Create a new transaction"""
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
        status: Optional[CategorizationStatus] = Query(
            None, description="Filter by categorization status"
        ),
    ):
        """Get all transactions with optional filtering"""
        # For now, we'll just get all transactions and filter in memory
        # In a real application, you'd want to add filtering to the repository
        transactions = internal.transaction_service.get_all_transactions()

        # Filter by category_id if provided
        if category_id is not None:
            transactions = [t for t in transactions if t.category_id == category_id]

        # Filter by categorization status if provided
        if status is not None:
            transactions = [
                t for t in transactions if t.categorization_status == status
            ]
        return TransactionListResponse(
            transactions=transactions,
            total=len(transactions),
        )

    @router.get("/{transaction_id}", response_model=TransactionResponse)
    def get_transaction(transaction_id: UUID):
        """Get a transaction by ID"""
        transaction = internal.transaction_service.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return transaction

    @router.put("/{transaction_id}", response_model=TransactionResponse)
    def update_transaction(transaction_id: UUID, transaction_data: TransactionUpdate):
        """Update a transaction"""
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
    def delete_transaction(transaction_id: UUID):
        """Delete a transaction"""
        deleted = internal.transaction_service.delete_transaction(transaction_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )

    @router.put("/{transaction_id}/categorize", response_model=TransactionResponse)
    def categorize_transaction(
        transaction_id: UUID, category_id: Optional[UUID] = None
    ):
        """Categorize a transaction"""
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
    def mark_categorization_failure(transaction_id: UUID):
        """Mark a transaction as having failed categorization"""
        updated_transaction = internal.transaction_service.mark_categorization_failure(
            transaction_id=transaction_id,
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return updated_transaction

    # Include the router in the app with the API prefix from settings
    from app.core.config import settings

    app.include_router(router, prefix=settings.API_V1_STR)
