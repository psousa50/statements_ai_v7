from typing import List
from uuid import UUID

from fastapi import APIRouter, FastAPI, HTTPException, status

from app.api.schemas import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.core.dependencies import InternalDependencies


def register_transaction_routes(app: FastAPI, internal: InternalDependencies):
    """Register transaction routes with the FastAPI app."""
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
    def create_transaction(transaction_data: TransactionCreate):
        """Create a new transaction"""
        transaction = internal.transaction_service.create_transaction(
            transaction_date=transaction_data.date,
            description=transaction_data.description,
            amount=transaction_data.amount,
        )
        return transaction

    @router.get("", response_model=TransactionListResponse)
    def get_transactions():
        """Get all transactions"""
        transactions = internal.transaction_service.get_all_transactions()
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

    # Include the router in the app with the API prefix from settings
    from app.core.config import settings
    app.include_router(router, prefix=settings.API_V1_STR)
