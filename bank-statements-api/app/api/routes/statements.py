import logging
from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.schemas import StatementAnalysisResponse, StatementUploadRequest, StatementUploadResponse
from app.core.dependencies import InternalDependencies
from app.domain.dto.statement_processing import AnalysisResultDTO
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
            return StatementAnalysisResponse.model_validate(result)
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
            # Create AnalysisResultDTO from the request data
            analysis_result = AnalysisResultDTO(
                uploaded_file_id=upload_data.uploaded_file_id,
                file_type=upload_data.file_type,
                column_mapping=upload_data.column_mapping,
                header_row_index=upload_data.header_row_index,
                data_start_row_index=upload_data.data_start_row_index,
                file_hash=upload_data.file_hash,
                sample_data=None
            )

            # Handle source if provided
            if upload_data.source:
                try:
                    # Try to find existing source by name
                    source = internal.source_service.get_source_by_name(upload_data.source)

                    # If source doesn't exist, create it
                    if not source:
                        logger.info(f"Creating new source: {upload_data.source}")
                        source = internal.source_service.create_source(upload_data.source)
                    else:
                        logger.info(f"Using existing source: {upload_data.source}")

                    # Add source_id to the analysis result
                    analysis_result.source_id = str(source.id)
                except Exception as e:
                    log_exception("Error handling source: %s", str(e))
                    # Continue without source if there's an error

            result = internal.statement_persistence_service.persist(analysis_result)
            return StatementUploadResponse(
                uploaded_file_id=result.uploaded_file_id,
                transactions_saved=result.transactions_saved,
                success=True,
                message=f"Successfully saved {result.transactions_saved} transactions",
                sample_data=None,
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
