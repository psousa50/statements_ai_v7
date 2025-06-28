from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from app.api.schemas import CategoryCreate, CategoryListResponse, CategoryResponse, CategoryUpdate
from app.core.config import settings
from app.core.dependencies import InternalDependencies


def register_category_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    """Register category routes with the FastAPI app."""
    router = APIRouter(prefix="/categories", tags=["categories"])

    @router.post(
        "",
        response_model=CategoryResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_category(
        category_data: CategoryCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Create a new category"""
        try:
            category = internal.category_service.create_category(
                name=category_data.name,
                parent_id=category_data.parent_id,
            )
            return category
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    @router.get("", response_model=CategoryListResponse)
    def get_categories(
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get all categories"""
        categories = internal.category_service.get_all_categories()
        return CategoryListResponse(
            categories=categories,
            total=len(categories),
        )

    @router.get("/root", response_model=CategoryListResponse)
    def get_root_categories(
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get all root categories (categories without a parent)"""
        categories = internal.category_service.get_root_categories()
        return CategoryListResponse(
            categories=categories,
            total=len(categories),
        )

    @router.get("/{category_id}", response_model=CategoryResponse)
    def get_category(
        category_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get a category by ID"""
        category = internal.category_service.get_category(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )
        return category

    @router.get(
        "/{category_id}/subcategories",
        response_model=CategoryListResponse,
    )
    def get_subcategories(
        category_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get all subcategories for a given parent category"""
        try:
            subcategories = internal.category_service.get_subcategories(category_id)
            return CategoryListResponse(
                categories=subcategories,
                total=len(subcategories),
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    @router.put("/{category_id}", response_model=CategoryResponse)
    def update_category(
        category_id: UUID,
        category_data: CategoryUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Update a category"""
        try:
            updated_category = internal.category_service.update_category(
                category_id=category_id,
                name=category_data.name,
                parent_id=category_data.parent_id,
            )
            if not updated_category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found",
                )
            return updated_category
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    @router.delete(
        "/{category_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_category(
        category_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Delete a category"""
        try:
            deleted = internal.category_service.delete_category(category_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found",
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    app.include_router(router, prefix=settings.API_V1_STR)
