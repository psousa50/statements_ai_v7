from datetime import date, timedelta
from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from app.api.routes.auth import require_current_user
from app.api.schemas import FilterPresetCreate, FilterPresetData, FilterPresetListResponse, FilterPresetResponse
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.filter_preset import FilterPreset
from app.domain.models.user import User


def _to_response_with_adjusted_dates(preset: FilterPreset) -> FilterPresetResponse:
    filter_data = dict(preset.filter_data)

    if filter_data.get("is_relative") and filter_data.get("anchor_date"):
        anchor = date.fromisoformat(filter_data["anchor_date"])
        today = date.today()
        offset = (today - anchor).days

        if offset != 0:
            original_start = date.fromisoformat(filter_data["start_date"])
            original_end = date.fromisoformat(filter_data["end_date"])
            filter_data["start_date"] = (original_start + timedelta(days=offset)).isoformat()
            filter_data["end_date"] = (original_end + timedelta(days=offset)).isoformat()

    return FilterPresetResponse(
        id=preset.id,
        name=preset.name,
        filter_data=FilterPresetData.model_validate(filter_data),
        created_at=preset.created_at,
        updated_at=preset.updated_at,
    )


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
            filter_data=preset_data.filter_data.model_dump(mode="json", exclude_none=True),
        )
        return FilterPresetResponse.model_validate(preset)

    @router.get("", response_model=FilterPresetListResponse)
    def list_filter_presets(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        presets = internal.filter_preset_repository.get_all_by_user(current_user.id)
        return FilterPresetListResponse(
            presets=[_to_response_with_adjusted_dates(p) for p in presets],
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
        return _to_response_with_adjusted_dates(preset)

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
