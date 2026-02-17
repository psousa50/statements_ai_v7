from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, status

from app.api.routes.auth import require_current_user
from app.api.schemas import TagCreate, TagListResponse, TagResponse, TransactionResponse
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User


def register_tag_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    tag_router = APIRouter(prefix="/tags", tags=["tags"])

    @tag_router.get("", response_model=TagListResponse)
    def get_tags(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        tags = internal.tag_service.get_all_tags(current_user.id)
        return TagListResponse(tags=tags, total=len(tags))

    @tag_router.post(
        "",
        response_model=TagResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_tag(
        tag_data: TagCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        return internal.tag_service.create_tag(
            name=tag_data.name,
            user_id=current_user.id,
        )

    app.include_router(tag_router, prefix=settings.API_V1_STR)

    transaction_tag_router = APIRouter(prefix="/transactions", tags=["transaction-tags"])

    @transaction_tag_router.post(
        "/{transaction_id}/tags/{tag_id}",
        response_model=TransactionResponse,
    )
    def add_tag_to_transaction(
        transaction_id: UUID,
        tag_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        return internal.tag_service.add_tag_to_transaction(
            transaction_id=transaction_id,
            tag_id=tag_id,
            user_id=current_user.id,
        )

    @transaction_tag_router.delete(
        "/{transaction_id}/tags/{tag_id}",
        response_model=TransactionResponse,
    )
    def remove_tag_from_transaction(
        transaction_id: UUID,
        tag_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        return internal.tag_service.remove_tag_from_transaction(
            transaction_id=transaction_id,
            tag_id=tag_id,
            user_id=current_user.id,
        )

    app.include_router(transaction_tag_router, prefix=settings.API_V1_STR)
