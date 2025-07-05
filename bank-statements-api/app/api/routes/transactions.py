from datetime import date
from decimal import Decimal
from typing import Callable, Iterator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status

from app.api.schemas import (
    BulkUpdateTransactionsRequest,
    BulkUpdateTransactionsResponse,
    CategoryTotalResponse,
    CategoryTotalsResponse,
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdateRequest,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.transaction import CategorizationStatus


def register_transaction_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.post(
        "",
        response_model=TransactionResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_transaction(
        transaction_data: TransactionCreateRequest,
        after_transaction_id: Optional[UUID] = Query(
            None,
            description="Insert after this transaction ID for ordering",
        ),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Create a manual transaction with proper ordering.
        If after_transaction_id is provided, the new transaction will be inserted after that transaction.
        Otherwise, it will be added at the end of the day's transactions.
        """
        transaction = internal.transaction_service.create_transaction(
            transaction_data=transaction_data,
            after_transaction_id=after_transaction_id,
        )
        return transaction

    @router.get("", response_model=TransactionListResponse)
    def get_transactions(
        page: int = Query(1, ge=1, description="Page number (1-based)"),
        page_size: int = Query(
            20,
            ge=1,
            le=100,
            description="Number of transactions per page",
        ),
        category_ids: Optional[str] = Query(
            None,
            description="Comma-separated list of category IDs",
        ),
        status: Optional[CategorizationStatus] = Query(
            None,
            description="Filter by categorization status",
        ),
        min_amount: Optional[Decimal] = Query(None, description="Minimum transaction amount"),
        max_amount: Optional[Decimal] = Query(None, description="Maximum transaction amount"),
        description_search: Optional[str] = Query(
            None,
            description="Search in transaction description",
        ),
        account_id: Optional[UUID] = Query(None, description="Filter by account ID"),
        start_date: Optional[date] = Query(
            None,
            description="Filter transactions from this date",
        ),
        end_date: Optional[date] = Query(
            None,
            description="Filter transactions to this date",
        ),
        include_running_balance: bool = Query(
            False,
            description="Include running balance in response",
        ),
        sort_field: Optional[str] = Query(
            None,
            description="Field to sort by (date, amount, description, created_at)",
        ),
        sort_direction: Optional[str] = Query(None, description="Sort direction (asc, desc)"),
        enhancement_rule_id: Optional[UUID] = Query(
            None,
            description="Filter by enhancement rule ID (overrides other filters)",
        ),
        exclude_transfers: Optional[bool] = Query(
            True,
            description="Exclude transfers between accounts",
        ),
        transaction_type: Optional[str] = Query(
            None,
            description="Filter by transaction type: 'debit', 'credit', or 'all'",
        ),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        # If enhancement_rule_id is provided, use rule-based filtering
        if enhancement_rule_id:
            transactions = internal.transaction_service.get_transactions_matching_rule_paginated(
                enhancement_rule_id=enhancement_rule_id,
                page=page,
                page_size=page_size,
                sort_field=sort_field,
                sort_direction=sort_direction,
                include_running_balance=include_running_balance,
            )
            return transactions

        # Parse category_ids if provided
        parsed_category_ids = None
        if category_ids:
            try:
                parsed_category_ids = [UUID(cid.strip()) for cid in category_ids.split(",") if cid.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid category IDs format",
                )

        transactions = internal.transaction_service.get_transactions_paginated(
            page=page,
            page_size=page_size,
            category_ids=parsed_category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            include_running_balance=include_running_balance,
            sort_field=sort_field,
            sort_direction=sort_direction,
            exclude_transfers=exclude_transfers,
            transaction_type=transaction_type,
        )
        return transactions

    @router.get(
        "/category-totals",
        response_model=CategoryTotalsResponse,
    )
    def get_category_totals(
        category_ids: Optional[str] = Query(
            None,
            description="Comma-separated list of category IDs",
        ),
        status: Optional[CategorizationStatus] = Query(
            None,
            description="Filter by categorization status",
        ),
        min_amount: Optional[Decimal] = Query(None, description="Minimum transaction amount"),
        max_amount: Optional[Decimal] = Query(None, description="Maximum transaction amount"),
        description_search: Optional[str] = Query(
            None,
            description="Search in transaction description",
        ),
        account_id: Optional[UUID] = Query(None, description="Filter by source ID"),
        start_date: Optional[date] = Query(
            None,
            description="Filter transactions from this date",
        ),
        end_date: Optional[date] = Query(
            None,
            description="Filter transactions to this date",
        ),
        exclude_transfers: Optional[bool] = Query(
            True,
            description="Exclude transfers between accounts",
        ),
        transaction_type: Optional[str] = Query(
            None,
            description="Filter by transaction type: 'debit', 'credit', or 'all'",
        ),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get aggregated totals per category for chart data. Uses the same filtering options as get_transactions."""
        # Parse category_ids if provided
        parsed_category_ids = None
        if category_ids:
            try:
                parsed_category_ids = [UUID(cid.strip()) for cid in category_ids.split(",") if cid.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid category IDs format",
                )

        totals_dict = internal.transaction_service.get_category_totals(
            category_ids=parsed_category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
            transaction_type=transaction_type,
        )

        # Convert to response format
        totals = [
            CategoryTotalResponse(
                category_id=category_id,
                total_amount=values["total_amount"],
                transaction_count=int(values["transaction_count"]),
            )
            for category_id, values in totals_dict.items()
        ]

        return CategoryTotalsResponse(totals=totals)

    # Bulk update route - MUST be defined before /{transaction_id} routes to avoid path conflicts
    @router.put(
        "/bulk-update-category",
        response_model=BulkUpdateTransactionsResponse,
    )
    def bulk_update_transaction_category(
        request: BulkUpdateTransactionsRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Update the category for all transactions with the given normalized description
        """
        try:
            # Convert category_id string to UUID if provided
            category_uuid = None
            if request.category_id:
                try:
                    category_uuid = UUID(request.category_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid UUID format for category_id: {request.category_id}",
                    )

            updated_count = internal.transaction_service.bulk_update_category_by_normalized_description(
                normalized_description=request.normalized_description,
                category_id=category_uuid,
            )

            action = "categorized" if request.category_id else "uncategorized"
            message = f"Successfully {action} {updated_count} transactions with description '{request.normalized_description}'"

            return BulkUpdateTransactionsResponse(updated_count=updated_count, message=message)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating transactions: {str(e)}",
            )

    @router.get(
        "/{transaction_id}",
        response_model=TransactionResponse,
    )
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

    @router.put(
        "/{transaction_id}",
        response_model=TransactionResponse,
    )
    def update_transaction(
        transaction_id: UUID,
        transaction_data: TransactionUpdateRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        updated_transaction = internal.transaction_service.update_transaction(
            transaction_id=transaction_id,
            transaction_date=transaction_data.date,
            description=transaction_data.description,
            amount=transaction_data.amount,
            account_id=transaction_data.account_id,
            category_id=transaction_data.category_id,
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return updated_transaction

    @router.delete(
        "/{transaction_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
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

    @router.put(
        "/{transaction_id}/categorize",
        response_model=TransactionResponse,
    )
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

    @router.put(
        "/{transaction_id}/mark-failure",
        response_model=TransactionResponse,
    )
    def mark_categorization_failure(
        transaction_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        updated_transaction = internal.transaction_service.mark_categorization_failure(transaction_id=transaction_id)
        if not updated_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return updated_transaction

    app.include_router(router, prefix=settings.API_V1_STR)
