import logging
from typing import Callable, Iterator
from uuid import UUID

from app.api.schemas import (
    BackgroundJobInfoResponse,
    JobStatusResponse,
    StatementAnalysisResponse,
    StatementUploadRequest,
    StatementUploadResponse,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.dto.statement_processing import PersistenceRequestDTO
from app.logging.utils import log_exception
from app.workers.job_processor import process_pending_jobs
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status,
)

logger = logging.getLogger("app")


def register_statement_routes(
    app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]
):
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
        background_tasks: BackgroundTasks,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Statement upload endpoint with immediate rule-based categorization
        and background AI processing for unmatched transactions.
        """
        try:
            # Step 1: Persist statement and transactions
            persistence_request = PersistenceRequestDTO(
                source_id=UUID(upload_data.source_id),
                uploaded_file_id=upload_data.uploaded_file_id,
                column_mapping=upload_data.column_mapping,
                header_row_index=upload_data.header_row_index,
                data_start_row_index=upload_data.data_start_row_index,
            )

            persistence_result = internal.statement_persistence_service.persist(
                persistence_request
            )

            # Step 2: Get the persisted transactions for processing
            transactions = internal.transaction_service.transaction_repository.get_by_uploaded_file_id(
                UUID(upload_data.uploaded_file_id)
            )

            # Step 3: Process transactions with orchestrator
            sync_result = (
                internal.transaction_processing_orchestrator.process_transactions(
                    uploaded_file_id=UUID(upload_data.uploaded_file_id),
                    transactions=transactions,
                )
            )

            # Step 4: Build response with sync results
            response = StatementUploadResponse(
                uploaded_file_id=persistence_result.uploaded_file_id,
                transactions_saved=persistence_result.transactions_saved,
                success=True,
                message=f"Successfully processed {sync_result.total_processed} transactions. "
                f"{sync_result.rule_based_matches} matched by rules ({sync_result.match_rate_percentage}%).",
                total_processed=sync_result.total_processed,
                rule_based_matches=sync_result.rule_based_matches,
                match_rate_percentage=sync_result.match_rate_percentage,
                processing_time_ms=sync_result.processing_time_ms,
                background_job=None,
            )

            # Step 5: Add background job info if there are unmatched transactions
            if sync_result.has_unmatched_transactions:
                background_job_info = internal.transaction_processing_orchestrator.get_background_job_info(
                    job_id=UUID(upload_data.uploaded_file_id),  # Placeholder
                    status_url_template="/api/v1/transactions/categorization-jobs/{}/status",
                )

                if background_job_info:
                    response.background_job = BackgroundJobInfoResponse(
                        job_id=background_job_info.job_id,
                        status=background_job_info.status,
                        remaining_transactions=background_job_info.remaining_transactions,
                        estimated_completion_seconds=background_job_info.estimated_completion_seconds,
                        status_url=background_job_info.status_url,
                    )

                # Step 6: Trigger immediate background job processing
                background_tasks.add_task(process_pending_jobs, internal)

            return response

        except Exception as e:
            log_exception("Error processing statement: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing statement: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)


def register_transaction_job_routes(
    app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]
):
    """Register transaction job status routes for US-21"""
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.get(
        "/categorization-jobs/{job_id}/status", response_model=JobStatusResponse
    )
    async def get_job_status(
        job_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Get status of a background categorization job.

        Returns detailed progress information, estimated completion time,
        and results when the job is complete.
        """
        try:
            job_status = internal.background_job_service.get_job_status_for_api(job_id)

            if not job_status:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job with ID {job_id} not found",
                )

            return JobStatusResponse.model_validate(job_status)

        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error getting job status: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving job status: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)
