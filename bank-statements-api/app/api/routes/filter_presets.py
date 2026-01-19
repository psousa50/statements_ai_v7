from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from app.api.routes.auth import require_current_user
from app.api.schemas import FilterPresetCreate, FilterPresetListResponse, FilterPresetResponse
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User


def register_filter_preset_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/filter-presets", tags=["filter-presets"])

    @router.post(
        "",
        response_model=FilterPresetResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_filter_preset(
        preset_data: FilterPresetCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        preset = internal.filter_preset_repository.create(
            user_id=current_user.id,
            name=preset_data.name,
            filter_data=preset_data.filter_data.model_dump(exclude_none=True),
        )
        return FilterPresetResponse.model_validate(preset)

    @router.get("", response_model=FilterPresetListResponse)
    def list_filter_presets(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        presets = internal.filter_preset_repository.get_all_by_user(current_user.id)
        return FilterPresetListResponse(
            presets=[FilterPresetResponse.model_validate(p) for p in presets],
            total=len(presets),
        )

    @router.get("/{preset_id}", response_model=FilterPresetResponse)
    def get_filter_preset(
        preset_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        preset = internal.filter_preset_repository.get_by_id(preset_id, current_user.id)
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Filter preset with ID {preset_id} not found",
            )
        return FilterPresetResponse.model_validate(preset)

    @router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_filter_preset(
        preset_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        deleted = internal.filter_preset_repository.delete(preset_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Filter preset with ID {preset_id} not found",
            )
        return None

    app.include_router(router, prefix=settings.API_V1_STR)
