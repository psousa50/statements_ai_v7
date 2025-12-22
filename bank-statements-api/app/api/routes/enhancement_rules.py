from typing import Callable, Iterator, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status

from app.api.routes.auth import require_current_user
from app.api.schemas import (
    CleanupUnusedRulesResponse,
    EnhancementRuleCreate,
    EnhancementRuleListResponse,
    EnhancementRulePreview,
    EnhancementRuleResponse,
    EnhancementRuleStatsResponse,
    EnhancementRuleUpdate,
    MatchingTransactionsCountResponse,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.enhancement_rule import EnhancementRuleSource, MatchType
from app.domain.models.user import User
from app.services.enhancement_rule_management import EnhancementRuleManagementService


def register_enhancement_rule_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(
        prefix="/enhancement-rules",
        tags=["enhancement-rules"],
    )

    @router.get("", response_model=EnhancementRuleListResponse)
    def list_enhancement_rules(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(
            50,
            ge=1,
            le=100,
            description="Number of rules per page",
        ),
        description_search: Optional[str] = Query(None, description="Search in rule descriptions"),
        category_ids: Optional[List[UUID]] = Query(None, description="Filter by category IDs"),
        counterparty_account_ids: Optional[List[UUID]] = Query(
            None,
            description="Filter by counterparty account IDs",
        ),
        match_type: Optional[MatchType] = Query(None, description="Filter by match type"),
        source: Optional[EnhancementRuleSource] = Query(None, description="Filter by rule source"),
        show_invalid_only: Optional[bool] = Query(
            None, description="Show only invalid rules (rules with no category and no counterparty)"
        ),
        sort_field: str = Query("created_at", description="Field to sort by"),
        sort_direction: str = Query("desc", description="Sort direction (asc/desc)"),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ) -> EnhancementRuleListResponse:
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            offset = (page - 1) * page_size
            result = service.list_rules(
                user_id=current_user.id,
                limit=page_size,
                offset=offset,
                description_search=description_search,
                category_ids=category_ids,
                counterparty_account_ids=counterparty_account_ids,
                match_type=match_type,
                source=source,
                show_invalid_only=show_invalid_only,
                sort_field=sort_field,
                sort_direction=sort_direction,
            )

            return EnhancementRuleListResponse(
                rules=result["rules"],
                total=result["total"],
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list enhancement rules: {str(e)}",
            )

    @router.get(
        "/stats",
        response_model=EnhancementRuleStatsResponse,
    )
    def get_enhancement_rule_stats(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ) -> EnhancementRuleStatsResponse:
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            stats = service.get_stats(current_user.id)
            return EnhancementRuleStatsResponse(**stats)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get enhancement rule stats: {str(e)}",
            )

    @router.post(
        "/cleanup-unused",
        response_model=CleanupUnusedRulesResponse,
    )
    def cleanup_unused_rules(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ) -> CleanupUnusedRulesResponse:
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            result = service.cleanup_unused_rules(current_user.id)
            return CleanupUnusedRulesResponse(**result)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cleanup unused rules: {str(e)}",
            )

    @router.get(
        "/{rule_id}/matching-transactions/count",
        response_model=MatchingTransactionsCountResponse,
    )
    def get_matching_transactions_count(
        rule_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ) -> MatchingTransactionsCountResponse:
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            result = service.get_matching_transactions_count(rule_id, current_user.id)
            return MatchingTransactionsCountResponse(**result)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get matching transactions count: {str(e)}",
            )

    @router.post(
        "/preview/matching-transactions/count",
        response_model=MatchingTransactionsCountResponse,
    )
    def preview_matching_transactions_count(
        rule_preview: EnhancementRulePreview,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ) -> MatchingTransactionsCountResponse:
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            result = service.preview_matching_transactions_count(rule_preview, current_user.id)
            return MatchingTransactionsCountResponse(**result)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to preview matching transactions count: {str(e)}",
            )

    @router.get("/{rule_id}", response_model=EnhancementRuleResponse)
    def get_enhancement_rule(
        rule_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ) -> EnhancementRuleResponse:
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            rule = service.get_rule(rule_id, current_user.id)
            if not rule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Enhancement rule with ID {rule_id} not found",
                )

            return EnhancementRuleResponse.model_validate(rule)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get enhancement rule: {str(e)}",
            )

    @router.post(
        "",
        response_model=EnhancementRuleResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_enhancement_rule(
        rule_data: EnhancementRuleCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ) -> EnhancementRuleResponse:
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            rule = service.create_rule(
                user_id=current_user.id,
                normalized_description_pattern=rule_data.normalized_description_pattern,
                match_type=rule_data.match_type,
                category_id=rule_data.category_id,
                counterparty_account_id=rule_data.counterparty_account_id,
                min_amount=float(rule_data.min_amount) if rule_data.min_amount else None,
                max_amount=float(rule_data.max_amount) if rule_data.max_amount else None,
                start_date=rule_data.start_date,
                end_date=rule_data.end_date,
                source=rule_data.source,
            )

            return EnhancementRuleResponse.model_validate(rule)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create enhancement rule: {str(e)}",
            )

    @router.put("/{rule_id}", response_model=EnhancementRuleResponse)
    def update_enhancement_rule(
        rule_id: UUID,
        rule_data: EnhancementRuleUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ) -> EnhancementRuleResponse:
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            rule = service.update_rule(
                rule_id=rule_id,
                user_id=current_user.id,
                normalized_description_pattern=rule_data.normalized_description_pattern,
                match_type=rule_data.match_type,
                category_id=rule_data.category_id,
                counterparty_account_id=rule_data.counterparty_account_id,
                min_amount=float(rule_data.min_amount) if rule_data.min_amount else None,
                max_amount=float(rule_data.max_amount) if rule_data.max_amount else None,
                start_date=rule_data.start_date,
                end_date=rule_data.end_date,
                source=rule_data.source,
                apply_to_existing=rule_data.apply_to_existing,
            )

            if not rule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Enhancement rule with ID {rule_id} not found",
                )

            return EnhancementRuleResponse.model_validate(rule)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update enhancement rule: {str(e)}",
            )

    @router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_enhancement_rule(
        rule_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        service: EnhancementRuleManagementService = internal.enhancement_rule_management_service

        try:
            success = service.delete_rule(rule_id, current_user.id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Enhancement rule with ID {rule_id} not found",
                )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete enhancement rule: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)
