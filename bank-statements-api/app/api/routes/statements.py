import logging
from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.schemas import StatementAnalysisResponse, StatementUploadRequest, StatementUploadResponse
from app.core.dependencies import InternalDependencies
from app.domain.dto.statement_processing import PersistenceRequestDTO
from app.logging.utils import log_exception
from app.core.config import settings

logger = logging.getLogger("app")


def register_statement_routes(app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]):
    router = APIRouter(prefix="/statements", tags=["statements"])

    @router.post("/analyze", response_model=StatementAnalysisResponse)
    async def analyze_statement(
        file: UploadFile = File(...),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
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
        try:
            persistence_request = PersistenceRequestDTO(
                source_id=UUID(upload_data.source_id),
                uploaded_file_id=upload_data.uploaded_file_id,
                column_mapping=upload_data.column_mapping,
                header_row_index=upload_data.header_row_index,
                data_start_row_index=upload_data.data_start_row_index,
            )

            result = internal.statement_persistence_service.persist(persistence_request)
            return StatementUploadResponse(
                uploaded_file_id=result.uploaded_file_id,
                transactions_saved=result.transactions_saved,
                success=True,
                message=f"Successfully saved {result.transactions_saved} transactions",
            )
        except Exception as e:
            log_exception("Error processing statement: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing statement: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)
