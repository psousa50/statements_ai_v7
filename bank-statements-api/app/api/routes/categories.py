from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.schemas import CategoryCreate, CategoryListResponse, CategoryResponse, CategoryUpdate, CategoryUploadResponse
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

    @router.post(
        "/upload",
        response_model=CategoryUploadResponse,
        status_code=status.HTTP_200_OK,
    )
    async def upload_categories_csv(
        file: UploadFile = File(...),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Upload categories from CSV file with parent_name and name columns"""
        try:
            # Validate file type
            if not file.content_type or not file.content_type.startswith(("text/csv", "application/csv")):
                if not file.filename or not file.filename.lower().endswith(".csv"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File must be a CSV file",
                    )

            # Read file content
            content = await file.read()
            csv_content = content.decode("utf-8")

            # Get existing categories for comparison
            existing_categories = {(cat.name, cat.parent_id): cat for cat in internal.category_service.get_all_categories()}

            # Process CSV and upsert categories
            categories = internal.category_service.upsert_categories_from_csv(csv_content)

            # Calculate statistics
            categories_created = 0
            categories_found = 0
            for category in categories:
                if (category.name, category.parent_id) in existing_categories:
                    categories_found += 1
                else:
                    categories_created += 1

            return CategoryUploadResponse(
                categories_created=categories_created,
                categories_found=categories_found,
                total_processed=len(categories),
                categories=categories,
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading categories: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)
