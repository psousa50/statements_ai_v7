from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.api.schemas import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.core.database import get_db
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    """Dependency to get the transaction service with repository injection"""
    repository = SQLAlchemyTransactionRepository(db)
    return TransactionService(repository)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    transaction_service: TransactionService = Depends(get_transaction_service),
):
    """Create a new transaction"""
    transaction = transaction_service.create_transaction(
        transaction_date=transaction_data.date,
        description=transaction_data.description,
        amount=transaction_data.amount,
    )
    return transaction


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    transaction_service: TransactionService = Depends(get_transaction_service),
):
    """Get all transactions"""
    transactions = transaction_service.get_all_transactions()
    return TransactionListResponse(
        transactions=transactions,
        total=len(transactions),
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID,
    transaction_service: TransactionService = Depends(get_transaction_service),
):
    """Get a transaction by ID"""
    transaction = transaction_service.get_transaction(transaction_id)
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
    transaction_service: TransactionService = Depends(get_transaction_service),
):
    """Update a transaction"""
    updated_transaction = transaction_service.update_transaction(
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
def delete_transaction(
    transaction_id: UUID,
    transaction_service: TransactionService = Depends(get_transaction_service),
):
    """Delete a transaction"""
    deleted = transaction_service.delete_transaction(transaction_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found",
        )
