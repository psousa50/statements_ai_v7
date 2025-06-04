import logging
from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.schemas import BackgroundJobInfoResponse, JobStatusResponse, StatementAnalysisResponse, StatementUploadRequest, StatementUploadResponse
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.logging.utils import log_exception

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
        background_tasks: BackgroundTasks,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """
        Statement upload endpoint with immediate rule-based categorization
        and immediate background AI processing for unmatched transactions.
        """
        try:
            # Delegate to service with immediate background processing capability
            result = internal.statement_upload_service.upload_and_process(upload_data, background_tasks=background_tasks, internal_deps=internal)

            # Build HTTP response
            response = StatementUploadResponse(
                uploaded_file_id=result.uploaded_file_id,
                transactions_saved=result.transactions_saved,
                duplicated_transactions=result.duplicated_transactions,
                success=True,
                message=f"Successfully processed {result.total_processed} transactions. "
                f"{result.rule_based_matches} matched by rules ({result.match_rate_percentage}%). "
                f"{result.duplicated_transactions} duplicates found.",
                total_processed=result.total_processed,
                rule_based_matches=result.rule_based_matches,
                match_rate_percentage=result.match_rate_percentage,
                processing_time_ms=result.processing_time_ms,
                background_job=None,
            )

            # Add background job info if available
            if result.background_job_info:
                response.background_job = BackgroundJobInfoResponse(
                    job_id=result.background_job_info.job_id,
                    status=result.background_job_info.status,
                    remaining_transactions=result.background_job_info.remaining_transactions,
                    estimated_completion_seconds=result.background_job_info.estimated_completion_seconds,
                    status_url=result.background_job_info.status_url,
                )

            return response

        except Exception as e:
            log_exception("Error processing statement: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing statement: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)


def register_transaction_job_routes(app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]):
    """Register transaction job status routes for US-21"""
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.get("/categorization-jobs/{job_id}/status", response_model=JobStatusResponse)
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
