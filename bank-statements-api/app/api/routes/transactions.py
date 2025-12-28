from datetime import date
from decimal import Decimal
from typing import Callable, Iterator, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from starlette import status as http_status

from app.api.routes.auth import require_current_user
from app.api.schemas import (
    BulkReplaceCategoryRequest,
    BulkReplaceCategoryResponse,
    BulkUpdateTransactionsRequest,
    BulkUpdateTransactionsResponse,
    CategoryTimeSeriesDataPoint,
    CategoryTimeSeriesResponse,
    CategoryTotalResponse,
    CategoryTotalsResponse,
    CountSimilarResponse,
    EnhancementPreviewRequest,
    EnhancementPreviewResponse,
    RecurringPatternResponse,
    RecurringPatternsResponse,
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdateRequest,
)
from app.common.text_normalization import normalize_description
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.domain.models.user import User


def register_transaction_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.post(
        "",
        response_model=TransactionResponse,
        status_code=http_status.HTTP_201_CREATED,
    )
    def create_transaction(
        transaction_data: TransactionCreateRequest,
        after_transaction_id: Optional[UUID] = Query(
            None,
            description="Insert after this transaction ID for ordering",
        ),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        account = internal.account_service.get_account(transaction_data.account_id, current_user.id)
        if not account:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Account with ID {transaction_data.account_id} not found",
            )

        transaction = internal.transaction_service.create_transaction(
            user_id=current_user.id,
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
        exclude_uncategorized: Optional[bool] = Query(
            False,
            description="Exclude uncategorized transactions",
        ),
        transaction_type: Optional[str] = Query(
            None,
            description="Filter by transaction type: 'debit', 'credit', or 'all'",
        ),
        transaction_ids: Optional[str] = Query(
            None,
            description="Comma-separated list of transaction IDs to filter by",
        ),
        saved_filter_id: Optional[UUID] = Query(
            None,
            description="ID of a saved filter containing transaction IDs",
        ),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        if account_id:
            account = internal.account_service.get_account(account_id, current_user.id)
            if not account:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )

        if enhancement_rule_id:
            uncategorized_only = status == CategorizationStatus.UNCATEGORIZED
            transactions = internal.transaction_service.get_transactions_matching_rule_paginated(
                user_id=current_user.id,
                enhancement_rule_id=enhancement_rule_id,
                page=page,
                page_size=page_size,
                sort_field=sort_field,
                sort_direction=sort_direction,
                include_running_balance=include_running_balance,
                uncategorized_only=uncategorized_only,
            )
            return transactions

        parsed_category_ids = None
        if category_ids:
            try:
                parsed_category_ids = [UUID(cid.strip()) for cid in category_ids.split(",") if cid.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid category IDs format",
                )

        parsed_transaction_ids = None
        if saved_filter_id:
            saved_filter = internal.saved_filter_repository.get_by_id(saved_filter_id, current_user.id)
            if not saved_filter:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Saved filter with ID {saved_filter_id} not found or expired",
                )
            parsed_transaction_ids = [UUID(tid) for tid in saved_filter.filter_data.get("transaction_ids", [])]
        elif transaction_ids:
            try:
                parsed_transaction_ids = [UUID(tid.strip()) for tid in transaction_ids.split(",") if tid.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid transaction IDs format",
                )

        transactions = internal.transaction_service.get_transactions_paginated(
            user_id=current_user.id,
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
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
            transaction_ids=parsed_transaction_ids,
        )
        return transactions

    @router.get("/export")
    def export_transactions(
        category_ids: Optional[str] = Query(None),
        status: Optional[CategorizationStatus] = Query(None),
        min_amount: Optional[Decimal] = Query(None),
        max_amount: Optional[Decimal] = Query(None),
        description_search: Optional[str] = Query(None),
        account_id: Optional[UUID] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        sort_field: Optional[str] = Query(None),
        sort_direction: Optional[str] = Query(None),
        exclude_transfers: Optional[bool] = Query(True),
        exclude_uncategorized: Optional[bool] = Query(False),
        transaction_type: Optional[str] = Query(None),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        parsed_category_ids = None
        if category_ids:
            try:
                parsed_category_ids = [UUID(cid.strip()) for cid in category_ids.split(",") if cid.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category IDs format")

        response = internal.transaction_service.get_transactions_paginated(
            user_id=current_user.id,
            page=1,
            page_size=50000,
            category_ids=parsed_category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            sort_field=sort_field,
            sort_direction=sort_direction,
            exclude_transfers=exclude_transfers,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
        )

        all_categories = internal.category_repository.get_all(current_user.id)
        category_names = {c.id: c.name for c in all_categories}
        category_parents = {c.id: c.parent_id for c in all_categories}

        def get_full_category_name(category_id: UUID) -> str:
            if category_id not in category_names:
                return ""
            name = category_names[category_id]
            parent_id = category_parents.get(category_id)
            if parent_id and parent_id in category_names:
                return f"{category_names[parent_id]} > {name}"
            return name

        categories = {c.id: get_full_category_name(c.id) for c in all_categories}
        accounts = {a.id: a.name for a in internal.account_repository.get_all(current_user.id)}

        def escape_csv(value: str) -> str:
            escaped = value.replace('"', '""')
            if "," in escaped or '"' in escaped or "\n" in escaped:
                return f'"{escaped}"'
            return escaped

        rows = ["Date,Description,Amount,Category,Account\n"]
        for trx in response.transactions:
            category_name = categories.get(trx.category_id, "") if trx.category_id else ""
            account_name = accounts.get(trx.account_id, "") if trx.account_id else ""
            rows.append(
                f"{trx.date},{escape_csv(trx.description)},{trx.amount},{escape_csv(category_name)},{escape_csv(account_name)}\n"
            )

        filename = f"transactions-{date.today().isoformat()}.csv"
        return StreamingResponse(
            iter(rows),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

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
        exclude_uncategorized: Optional[bool] = Query(
            False,
            description="Exclude uncategorized transactions",
        ),
        transaction_type: Optional[str] = Query(
            None,
            description="Filter by transaction type: 'debit', 'credit', or 'all'",
        ),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
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
            user_id=current_user.id,
            category_ids=parsed_category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
        )

        totals = [
            CategoryTotalResponse(
                category_id=category_id,
                total_amount=values["total_amount"],
                transaction_count=int(values["transaction_count"]),
            )
            for category_id, values in totals_dict.items()
        ]

        return CategoryTotalsResponse(totals=totals)

    @router.get(
        "/category-time-series",
        response_model=CategoryTimeSeriesResponse,
    )
    def get_category_time_series(
        category_id: Optional[UUID] = Query(
            None,
            description="Category ID to fetch time series for (includes subcategories if root category)",
        ),
        period: str = Query("month", description="Time period grouping: 'month' or 'week'"),
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
        exclude_uncategorized: Optional[bool] = Query(
            False,
            description="Exclude uncategorized transactions",
        ),
        transaction_type: Optional[str] = Query(
            None,
            description="Filter by transaction type: 'debit', 'credit', or 'all'",
        ),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        parsed_category_ids = None
        if category_ids:
            try:
                parsed_category_ids = [UUID(cid.strip()) for cid in category_ids.split(",") if cid.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid category IDs format",
                )

        data_points = internal.transaction_service.get_category_time_series(
            user_id=current_user.id,
            category_id=category_id,
            period=period,
            category_ids=parsed_category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
        )

        response_data_points = [
            CategoryTimeSeriesDataPoint(
                period=dp["period"],
                category_id=dp["category_id"],
                total_amount=dp["total_amount"],
                transaction_count=dp["transaction_count"],
            )
            for dp in data_points
        ]

        return CategoryTimeSeriesResponse(data_points=response_data_points)

    @router.get(
        "/recurring-patterns",
        response_model=RecurringPatternsResponse,
    )
    def get_recurring_patterns(
        active_only: bool = Query(
            True,
            description="Only show patterns with recent transactions (last 90 days)",
        ),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        from dateutil.relativedelta import relativedelta

        lookback_start = date.today() - relativedelta(months=12)

        transactions_response = internal.transaction_service.get_transactions_paginated(
            user_id=current_user.id,
            page=1,
            page_size=10000,
            start_date=lookback_start,
            exclude_transfers=True,
            transaction_type="debit",
        )

        result = internal.recurring_expense_analyzer.analyze_patterns(
            transactions_response.transactions,
            user_id=current_user.id,
            active_only=active_only,
        )

        patterns_response = [RecurringPatternResponse(**pattern.to_dict()) for pattern in result.patterns]

        return RecurringPatternsResponse(
            patterns=patterns_response,
            summary=result.to_dict()["summary"],
        )

    @router.post(
        "/preview-enhancement",
        response_model=EnhancementPreviewResponse,
    )
    def preview_enhancement(
        request: EnhancementPreviewRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        normalized_desc = normalize_description(request.description)
        rules = internal.enhancement_rule_repository.find_matching_rules(normalized_desc, current_user.id)

        temp_transaction = Transaction(
            id=uuid4(),
            date=request.transaction_date or date.today(),
            description=request.description,
            normalized_description=normalized_desc,
            amount=request.amount or Decimal("0"),
            account_id=uuid4(),
            statement_id=None,
            source_type=SourceType.MANUAL,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
        )

        enhanced = internal.transaction_enhancer.apply_rules([temp_transaction], rules)
        enhanced_transaction = enhanced[0]

        if not enhanced_transaction.category_id and not enhanced_transaction.counterparty_account_id:
            return EnhancementPreviewResponse(matched=False)

        category_name = None
        if enhanced_transaction.category_id:
            category = internal.category_repository.get_by_id(enhanced_transaction.category_id, current_user.id)
            category_name = category.name if category else None

        counterparty_name = None
        if enhanced_transaction.counterparty_account_id:
            counterparty = internal.account_repository.get_by_id(enhanced_transaction.counterparty_account_id, current_user.id)
            counterparty_name = counterparty.name if counterparty else None

        matched_rule = None
        for rule in rules:
            if rule.normalized_description_pattern in normalized_desc:
                matched_rule = rule
                break

        return EnhancementPreviewResponse(
            matched=True,
            rule_pattern=matched_rule.normalized_description_pattern if matched_rule else normalized_desc,
            category_id=enhanced_transaction.category_id,
            category_name=category_name,
            counterparty_account_id=enhanced_transaction.counterparty_account_id,
            counterparty_account_name=counterparty_name,
        )

    @router.put(
        "/bulk-update-category",
        response_model=BulkUpdateTransactionsResponse,
    )
    def bulk_update_transaction_category(
        request: BulkUpdateTransactionsRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            category_uuid = None
            if request.category_id:
                try:
                    category_uuid = UUID(request.category_id)
                except ValueError:
                    raise HTTPException(
                        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid UUID format for category_id: {request.category_id}",
                    )

            updated_count = internal.transaction_service.bulk_update_category_by_normalized_description(
                user_id=current_user.id,
                normalized_description=request.normalized_description,
                category_id=category_uuid,
            )

            action = "categorized" if request.category_id else "uncategorized"
            message = f"Successfully {action} {updated_count} transactions with description '{request.normalized_description}'"

            return BulkUpdateTransactionsResponse(updated_count=updated_count, message=message)
        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating transactions: {str(e)}",
            )

    @router.get(
        "/count-similar",
        response_model=CountSimilarResponse,
    )
    def count_similar_transactions(
        normalized_description: str = Query(...),
        account_id: Optional[UUID] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        exclude_transfers: Optional[bool] = Query(None),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        count = internal.transaction_service.count_by_normalized_description(
            user_id=current_user.id,
            normalized_description=normalized_description,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
        )
        return CountSimilarResponse(count=count)

    @router.get(
        "/count-by-category",
        response_model=CountSimilarResponse,
    )
    def count_by_category(
        category_id: UUID = Query(...),
        account_id: Optional[UUID] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        exclude_transfers: Optional[bool] = Query(None),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        count = internal.transaction_service.count_by_category_id(
            user_id=current_user.id,
            category_id=category_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
        )
        return CountSimilarResponse(count=count)

    @router.put(
        "/bulk-replace-category",
        response_model=BulkReplaceCategoryResponse,
    )
    def bulk_replace_category(
        request: BulkReplaceCategoryRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        updated_count = internal.transaction_service.bulk_update_by_category_id(
            user_id=current_user.id,
            from_category_id=request.from_category_id,
            to_category_id=request.to_category_id,
            account_id=request.account_id,
            start_date=request.start_date,
            end_date=request.end_date,
            exclude_transfers=request.exclude_transfers,
        )

        from_category = internal.category_repository.get_by_id(request.from_category_id, current_user.id)
        from_name = from_category.name if from_category else "Unknown"

        if request.to_category_id:
            to_category = internal.category_repository.get_by_id(request.to_category_id, current_user.id)
            to_name = to_category.name if to_category else "Unknown"
            message = f"Replaced '{from_name}' with '{to_name}' for {updated_count} transactions"
        else:
            message = f"Removed '{from_name}' from {updated_count} transactions"

        return BulkReplaceCategoryResponse(updated_count=updated_count, message=message)

    @router.get(
        "/{transaction_id}",
        response_model=TransactionResponse,
    )
    def get_transaction(
        transaction_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        transaction = internal.transaction_service.get_transaction(transaction_id, current_user.id)
        if not transaction:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
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
        current_user: User = Depends(require_current_user),
    ):
        updated_transaction = internal.transaction_service.update_transaction(
            user_id=current_user.id,
            transaction_id=transaction_id,
            transaction_date=transaction_data.date,
            description=transaction_data.description,
            amount=transaction_data.amount,
            account_id=transaction_data.account_id,
            category_id=transaction_data.category_id,
            counterparty_account_id=transaction_data.counterparty_account_id,
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return updated_transaction

    @router.delete(
        "/{transaction_id}",
        status_code=http_status.HTTP_204_NO_CONTENT,
    )
    def delete_transaction(
        transaction_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        deleted = internal.transaction_service.delete_transaction(transaction_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
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
        current_user: User = Depends(require_current_user),
    ):
        updated_transaction = internal.transaction_service.categorize_transaction(
            user_id=current_user.id,
            transaction_id=transaction_id,
            category_id=category_id,
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
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
        current_user: User = Depends(require_current_user),
    ):
        updated_transaction = internal.transaction_service.mark_categorization_failure(
            transaction_id=transaction_id,
            user_id=current_user.id,
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )
        return updated_transaction

    app.include_router(router, prefix=settings.API_V1_STR)
