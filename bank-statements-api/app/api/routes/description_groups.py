from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from app.api.routes.auth import require_current_user
from app.api.schemas import (
    DescriptionGroupCreate,
    DescriptionGroupListResponse,
    DescriptionGroupResponse,
    DescriptionGroupUpdate,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User


def register_description_group_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/description-groups", tags=["description-groups"])

    @router.post(
        "",
        response_model=DescriptionGroupResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_group(
        group_data: DescriptionGroupCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            group = internal.description_group_service.create_group(
                user_id=current_user.id,
                name=group_data.name,
                normalized_descriptions=group_data.normalized_descriptions,
            )
            return group
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating group: {str(e)}",
            )

    @router.get("", response_model=DescriptionGroupListResponse)
    def get_all_groups(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            groups = internal.description_group_service.get_all_groups(current_user.id)
            return DescriptionGroupListResponse(groups=groups, total=len(groups))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error retrieving groups: {str(e)}",
            )

    @router.get("/{group_id}", response_model=DescriptionGroupResponse)
    def get_group(
        group_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            group = internal.description_group_service.get_group_by_id(group_id, current_user.id)
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Group with ID {group_id} not found",
                )
            return group
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error retrieving group: {str(e)}",
            )

    @router.put("/{group_id}", response_model=DescriptionGroupResponse)
    def update_group(
        group_id: UUID,
        group_data: DescriptionGroupUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            updated_group = internal.description_group_service.update_group(
                group_id=group_id,
                user_id=current_user.id,
                name=group_data.name,
                normalized_descriptions=group_data.normalized_descriptions,
            )
            if not updated_group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Group with ID {group_id} not found",
                )
            return updated_group
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating group: {str(e)}",
            )

    @router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_group(
        group_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            deleted = internal.description_group_service.delete_group(group_id, current_user.id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Group with ID {group_id} not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting group: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)
