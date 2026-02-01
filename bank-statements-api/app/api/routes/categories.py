from datetime import date
from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile, status
from starlette.responses import StreamingResponse

from app.api.routes.auth import require_current_user
from app.api.routes.feature_gate import require_feature
from app.api.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategorySuggestionResponse,
    CategoryUpdate,
    CategoryUploadResponse,
    CreateSelectedCategoriesRequest,
    CreateSelectedCategoriesResponse,
    GenerateCategoriesResponse,
    SubcategorySuggestionResponse,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User
from app.services.subscription import Feature


def register_category_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/categories", tags=["categories"])

    @router.post(
        "",
        response_model=CategoryResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_category(
        category_data: CategoryCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        return internal.category_service.create_category(
            name=category_data.name,
            user_id=current_user.id,
            parent_id=category_data.parent_id,
            color=category_data.color,
        )

    @router.get("", response_model=CategoryListResponse)
    def get_categories(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        categories = internal.category_service.get_all_categories(current_user.id)
        return CategoryListResponse(
            categories=categories,
            total=len(categories),
        )

    @router.get("/root", response_model=CategoryListResponse)
    def get_root_categories(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        categories = internal.category_service.get_root_categories(current_user.id)
        return CategoryListResponse(
            categories=categories,
            total=len(categories),
        )

    @router.get("/export")
    def export_categories(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        all_categories = internal.category_service.get_all_categories(current_user.id)
        category_names = {c.id: c.name for c in all_categories}

        def escape_csv(value: str) -> str:
            escaped = value.replace('"', '""')
            if "," in escaped or '"' in escaped or "\n" in escaped:
                return f'"{escaped}"'
            return escaped

        rows = ["parent_name,name,color\n"]
        for category in all_categories:
            parent_name = category_names.get(category.parent_id, "") if category.parent_id else ""
            color = category.color or ""
            rows.append(f"{escape_csv(parent_name)},{escape_csv(category.name)},{escape_csv(color)}\n")

        filename = f"categories-{date.today().isoformat()}.csv"
        return StreamingResponse(
            iter(rows),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @router.get("/{category_id}", response_model=CategoryResponse)
    def get_category(
        category_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        category = internal.category_service.get_category(category_id, current_user.id)
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
        current_user: User = Depends(require_current_user),
    ):
        subcategories = internal.category_service.get_subcategories(category_id, current_user.id)
        return CategoryListResponse(
            categories=subcategories,
            total=len(subcategories),
        )

    @router.put("/{category_id}", response_model=CategoryResponse)
    def update_category(
        category_id: UUID,
        category_data: CategoryUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        updated_category = internal.category_service.update_category(
            category_id=category_id,
            name=category_data.name,
            user_id=current_user.id,
            parent_id=category_data.parent_id,
            color=category_data.color,
        )
        if not updated_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )
        return updated_category

    @router.delete(
        "/{category_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_category(
        category_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        deleted = internal.category_service.delete_category(category_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

    @router.post(
        "/upload",
        response_model=CategoryUploadResponse,
        status_code=status.HTTP_200_OK,
    )
    async def upload_categories_csv(
        file: UploadFile = File(...),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        if not file.content_type or not file.content_type.startswith(("text/csv", "application/csv")):
            if not file.filename or not file.filename.lower().endswith(".csv"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be a CSV file",
                )

        content = await file.read()
        csv_content = content.decode("utf-8")

        existing_categories = {
            (cat.name, cat.parent_id): cat for cat in internal.category_service.get_all_categories(current_user.id)
        }

        categories = internal.category_service.upsert_categories_from_csv(csv_content, current_user.id)

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

    @router.post(
        "/ai/generate-suggestions",
        response_model=GenerateCategoriesResponse,
        status_code=status.HTTP_200_OK,
    )
    def generate_category_suggestions(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        require_feature(internal.subscription_service, current_user.id, Feature.AI_CATEGORISATION)

        result = internal.llm_category_generator.generate_suggestions(
            user_id=current_user.id,
        )

        suggestions = [
            CategorySuggestionResponse(
                parent_name=s.parent_name,
                parent_id=s.parent_id,
                parent_is_new=s.parent_is_new,
                subcategories=[SubcategorySuggestionResponse(name=sub.name, is_new=sub.is_new) for sub in s.subcategories],
                confidence=s.confidence,
                matched_descriptions=s.matched_descriptions,
            )
            for s in result.suggestions
        ]

        return GenerateCategoriesResponse(
            suggestions=suggestions,
            total_descriptions_analysed=result.total_descriptions_analysed,
        )

    @router.post(
        "/ai/create-selected",
        response_model=CreateSelectedCategoriesResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_selected_categories(
        request: CreateSelectedCategoriesRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        created_categories = []

        for selection in request.selections:
            if selection.parent_id:
                parent = internal.category_service.get_category(selection.parent_id, current_user.id)
            else:
                parent = internal.category_service.upsert_category(
                    name=selection.parent_name,
                    user_id=current_user.id,
                )
                if parent not in created_categories:
                    created_categories.append(parent)

            for sub_name in selection.subcategory_names:
                sub = internal.category_service.upsert_category(
                    name=sub_name,
                    user_id=current_user.id,
                    parent_id=parent.id,
                )
                if sub not in created_categories:
                    created_categories.append(sub)

        return CreateSelectedCategoriesResponse(
            categories_created=len(created_categories),
            categories=created_categories,
        )

    app.include_router(router, prefix=settings.API_V1_STR)
