from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from app.api.routes.auth import require_current_user
from app.api.schemas import SavedFilterCreate, SavedFilterResponse
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User


def register_saved_filter_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/saved-filters", tags=["saved-filters"])

    @router.post(
        "",
        response_model=SavedFilterResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_saved_filter(
        filter_data: SavedFilterCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        internal.saved_filter_repository.delete_expired(current_user.id)

        saved_filter = internal.saved_filter_repository.create(
            user_id=current_user.id,
            filter_data={"transaction_ids": [str(tid) for tid in filter_data.transaction_ids]},
        )
        return SavedFilterResponse.from_model(saved_filter)

    @router.get("/{filter_id}", response_model=SavedFilterResponse)
    def get_saved_filter(
        filter_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        saved_filter = internal.saved_filter_repository.get_by_id(filter_id, current_user.id)
        if not saved_filter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved filter with ID {filter_id} not found or expired",
            )
        return SavedFilterResponse.from_model(saved_filter)

    app.include_router(router, prefix=settings.API_V1_STR)
