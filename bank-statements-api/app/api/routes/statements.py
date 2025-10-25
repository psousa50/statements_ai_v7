import logging
from typing import Callable, Iterator, List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.schemas import (
    BackgroundJobInfoResponse,
    FilterConditionRequest,
    JobStatusResponse,
    StatementAnalysisResponse,
    StatementResponse,
    StatementUploadRequest,
    StatementUploadResponse,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.dto.statement_processing import FilterOperator
from app.logging.utils import log_exception

logger = logging.getLogger("app")


def register_statement_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
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

            # Convert FilterCondition objects to FilterConditionRequest for API response
            suggested_filters = []
            if result.suggested_filters:
                for filter_condition in result.suggested_filters:
                    suggested_filters.append(
                        FilterConditionRequest(
                            column_name=filter_condition.column_name,
                            operator=filter_condition.operator,
                            value=filter_condition.value,
                            case_sensitive=filter_condition.case_sensitive,
                        )
                    )

            # Convert saved row filters to FilterConditionRequest objects for API response
            saved_row_filters = None
            if result.saved_row_filters:
                saved_row_filters = []
                for filter_dict in result.saved_row_filters:
                    saved_row_filters.append(
                        FilterConditionRequest(
                            column_name=filter_dict["column_name"],
                            operator=FilterOperator(filter_dict["operator"]),
                            value=filter_dict.get("value"),
                            case_sensitive=filter_dict.get("case_sensitive", False),
                        )
                    )

            # Create response with converted filters
            response_data = {
                "uploaded_file_id": result.uploaded_file_id,
                "file_type": result.file_type,
                "column_mapping": result.column_mapping,
                "header_row_index": result.header_row_index,
                "data_start_row_index": result.data_start_row_index,
                "sample_data": result.sample_data,
                "account_id": result.account_id,
                "total_transactions": result.total_transactions,
                "unique_transactions": result.unique_transactions,
                "duplicate_transactions": result.duplicate_transactions,
                "date_range": result.date_range,
                "total_amount": result.total_amount,
                "total_debit": result.total_debit,
                "total_credit": result.total_credit,
                "suggested_filters": suggested_filters,
                "saved_row_filters": saved_row_filters,
            }

            return StatementAnalysisResponse.model_validate(response_data)
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
            result = internal.statement_upload_service.upload_statement(
                upload_data,
                background_tasks=background_tasks,
                internal_deps=internal,
            )

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
                    job_id=str(result.background_job_info.job_id),
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

    @router.get("", response_model=List[StatementResponse])
    async def list_statements(
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get all statements"""
        try:
            statements = internal.statement_service.get_all_statements()
            return [
                StatementResponse(
                    id=stmt.id,
                    account_id=stmt.account_id,
                    account_name=stmt.account.name,
                    filename=stmt.filename,
                    file_type=stmt.file_type,
                    transaction_count=stmt.transaction_count,
                    date_from=stmt.date_from,
                    date_to=stmt.date_to,
                    created_at=stmt.created_at,
                )
                for stmt in statements
            ]
        except Exception as e:
            log_exception("Error listing statements: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing statements: {str(e)}",
            )

    @router.delete("/{statement_id}")
    async def delete_statement(
        statement_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Delete a statement and all its transactions"""
        try:
            result = internal.statement_service.delete_statement_with_transactions(statement_id)
            return result
        except ValueError as e:
            # Statement not found
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            log_exception("Error deleting statement: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting statement: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)


def register_transaction_job_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    """Register transaction job status routes for US-21"""
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.get(
        "/categorization-jobs/{job_id}/status",
        response_model=JobStatusResponse,
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
