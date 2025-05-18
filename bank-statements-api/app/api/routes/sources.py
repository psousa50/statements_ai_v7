from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from app.api.schemas import SourceCreate, SourceListResponse, SourceResponse, SourceUpdate
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.logging.utils import log_exception


def register_source_routes(app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]):
    """Register source routes with the FastAPI app."""
    router = APIRouter(prefix="/sources", tags=["sources"])

    @router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
    async def create_source(
        source_data: SourceCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Create a new source"""
        try:
            # Check if source with the same name already exists
            existing_source = internal.source_service.get_source_by_name(source_data.name)
            if existing_source:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Source with name '{source_data.name}' already exists",
                )

            source = internal.source_service.create_source(source_data.name)
            return source
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error creating source: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating source: {str(e)}",
            )

    @router.get("", response_model=SourceListResponse)
    async def get_all_sources(
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get all sources"""
        try:
            sources = internal.source_service.get_all_sources()
            return SourceListResponse(sources=sources, total=len(sources))
        except Exception as e:
            log_exception("Error retrieving sources: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error retrieving sources: {str(e)}",
            )

    @router.get("/{source_id}", response_model=SourceResponse)
    async def get_source(
        source_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get a source by ID"""
        try:
            source = internal.source_service.get_source_by_id(source_id)
            if not source:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source with ID {source_id} not found",
                )
            return source
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error retrieving source: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error retrieving source: {str(e)}",
            )

    @router.put("/{source_id}", response_model=SourceResponse)
    async def update_source(
        source_id: UUID,
        source_data: SourceUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Update a source"""
        try:
            # Check if source exists
            existing_source = internal.source_service.get_source_by_id(source_id)
            if not existing_source:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source with ID {source_id} not found",
                )

            # Check if name is already taken by another source
            name_exists = internal.source_service.get_source_by_name(source_data.name)
            if name_exists and name_exists.id != source_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Source with name '{source_data.name}' already exists",
                )

            updated_source = internal.source_service.update_source(source_id, source_data.name)
            return updated_source
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error updating source: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating source: {str(e)}",
            )

    @router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_source(
        source_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Delete a source"""
        try:
            # Check if source exists
            existing_source = internal.source_service.get_source_by_id(source_id)
            if not existing_source:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source with ID {source_id} not found",
                )

            internal.source_service.delete_source(source_id)
            return None
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error deleting source: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting source: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)
