from typing import Callable, Iterator

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.schemas import StatementAnalysisResponse, StatementUploadRequest, StatementUploadResponse
from app.core.dependencies import InternalDependencies
import logging
from app.logging.utils import log_exception


logger = logging.getLogger("app")


def register_statement_routes(app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]):
    """Register statement routes with the FastAPI app."""
    router = APIRouter(prefix="/statements", tags=["statements"])

    @router.post("/analyze", response_model=StatementAnalysisResponse)
    async def analyze_statement(
        file: UploadFile = File(...),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Analyze a statement file and return column mappings and sample data"""
        try:
            file_content = await file.read()
            result = internal.statement_analyzer_service.analyze(
                filename=file.filename,
                file_content=file_content,
            )
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error analyzing file: {str(e)}",
            )

    @router.post("/upload", response_model=StatementUploadResponse)
    async def upload_statement(
        upload_data: StatementUploadRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Process and persist the analyzed statement data"""
        try:
            data = upload_data.model_dump()
            
            # Handle source if provided
            if upload_data.source:
                # Try to find existing source by name
                source = internal.source_service.get_source_by_name(upload_data.source)
                
                # If source doesn't exist, create it
                if not source:
                    source = internal.source_service.create_source(upload_data.source)
                
                # Add source_id to the data
                data["source_id"] = source.id
            
            result = internal.statement_persistence_service.persist(data)
            return StatementUploadResponse(
                uploaded_file_id=result["uploaded_file_id"],
                transactions_saved=result["transactions_saved"],
                success=True,
                message=f"Successfully saved {result['transactions_saved']} transactions",
            )
        except Exception as e:
            log_exception("Error processing statement: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing statement: {str(e)}",
            )

    # Include the router in the app with the API prefix from settings
    from app.core.config import settings

    app.include_router(router, prefix=settings.API_V1_STR)
