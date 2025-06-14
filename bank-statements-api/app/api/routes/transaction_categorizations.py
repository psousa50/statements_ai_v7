from typing import Callable, Iterator, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.api.schemas import (
    TransactionCategorizationCreate,
    TransactionCategorizationListResponse,
    TransactionCategorizationResponse,
    TransactionCategorizationStatsResponse,
    TransactionCategorizationUpdate,
)
from app.core.dependencies import InternalDependencies
from app.domain.models.transaction_categorization import CategorizationSource


def register_transaction_categorization_routes(
    app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]
):
    router = APIRouter(prefix="/transaction-categorizations", tags=["Transaction Categorizations"])

    @router.get("/", response_model=TransactionCategorizationListResponse)
    async def list_transaction_categorizations(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Number of rules per page"),
        description_search: Optional[str] = Query(None, description="Search in normalized descriptions"),
        category_ids: Optional[List[str]] = Query(None, description="Filter by category IDs"),
        source: Optional[CategorizationSource] = Query(None, description="Filter by categorization source"),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Get paginated list of transaction categorization rules with filtering.

        - **page**: Page number (1-based)
        - **page_size**: Number of rules per page (max 100)
        - **description_search**: Search term for normalized descriptions
        - **category_ids**: List of category IDs to filter by
        - **source**: Filter by categorization source (MANUAL or AI)
        """
        try:
            rules, total = internal.transaction_categorization_management_service.get_rules_paginated(
                page=page,
                page_size=page_size,
                description_search=description_search,
                category_ids=category_ids,
                source=source,
            )

            # Convert to response format with transaction counts
            rule_responses = []
            for rule in rules:
                rule_response = TransactionCategorizationResponse(
                    id=rule.id,
                    normalized_description=rule.normalized_description,
                    category_id=rule.category_id,
                    source=rule.source,
                    created_at=rule.created_at,
                    updated_at=rule.updated_at,
                    category=rule.category,
                    transaction_count=getattr(rule, "transaction_count", 0),
                )
                rule_responses.append(rule_response)

            return TransactionCategorizationListResponse(
                categorizations=rule_responses,
                total=total,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve transaction categorizations: {str(e)}",
            )

    @router.get("/stats", response_model=TransactionCategorizationStatsResponse)
    async def get_transaction_categorization_stats(
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Get enhanced statistics for transaction categorization rules.

        Returns comprehensive statistics including:
        - Summary counts (total rules, manual vs AI, transaction coverage)
        - Category usage breakdown
        - Top rules by transaction volume
        - Unused rules for cleanup
        """
        try:
            stats = internal.transaction_categorization_management_service.get_enhanced_statistics()
            return TransactionCategorizationStatsResponse(**stats)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve statistics: {str(e)}",
            )

    @router.get("/{rule_id}", response_model=TransactionCategorizationResponse)
    async def get_transaction_categorization(
        rule_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get a specific transaction categorization rule by ID."""
        rule = internal.transaction_categorization_management_service.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction categorization rule not found",
            )

        return TransactionCategorizationResponse(
            id=rule.id,
            normalized_description=rule.normalized_description,
            category_id=rule.category_id,
            source=rule.source,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            category=rule.category,
        )

    @router.post("/", response_model=TransactionCategorizationResponse, status_code=status.HTTP_201_CREATED)
    async def create_transaction_categorization(
        rule_data: TransactionCategorizationCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Create a new transaction categorization rule.

        - **normalized_description**: The normalized transaction description pattern
        - **category_id**: The category to assign to matching transactions
        - **source**: The source of this rule (MANUAL or AI)
        """
        try:
            rule = internal.transaction_categorization_management_service.create_rule(
                normalized_description=rule_data.normalized_description,
                category_id=rule_data.category_id,
                source=rule_data.source,
            )

            return TransactionCategorizationResponse(
                id=rule.id,
                normalized_description=rule.normalized_description,
                category_id=rule.category_id,
                source=rule.source,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
                category=rule.category,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A rule with this normalized description already exists",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create transaction categorization rule: {str(e)}",
            )

    @router.put("/{rule_id}", response_model=TransactionCategorizationResponse)
    async def update_transaction_categorization(
        rule_id: UUID,
        rule_data: TransactionCategorizationUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Update an existing transaction categorization rule.

        - **normalized_description**: The normalized transaction description pattern
        - **category_id**: The category to assign to matching transactions
        - **source**: The source of this rule (MANUAL or AI)
        """
        try:
            rule = internal.transaction_categorization_management_service.update_rule(
                rule_id=rule_id,
                normalized_description=rule_data.normalized_description,
                category_id=rule_data.category_id,
                source=rule_data.source,
            )

            if not rule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction categorization rule not found",
                )

            return TransactionCategorizationResponse(
                id=rule.id,
                normalized_description=rule.normalized_description,
                category_id=rule.category_id,
                source=rule.source,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
                category=rule.category,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A rule with this normalized description already exists",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update transaction categorization rule: {str(e)}",
            )

    @router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_transaction_categorization(
        rule_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Delete a transaction categorization rule."""
        success = internal.transaction_categorization_management_service.delete_rule(rule_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction categorization rule not found",
            )

    @router.post("/cleanup-unused", status_code=status.HTTP_200_OK)
    async def cleanup_unused_rules(
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Delete all categorization rules that are not being used by any transactions.

        This is a bulk operation that removes rules with zero transaction matches,
        helping to clean up unused categorization patterns.

        Returns the number of rules that were deleted.
        """
        try:
            deleted_count = internal.transaction_categorization_management_service.bulk_delete_unused_rules()
            return {
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} unused categorization rules",
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cleanup unused rules: {str(e)}",
            )

    app.include_router(router, prefix="/api/v1")
