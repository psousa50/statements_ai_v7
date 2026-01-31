import logging
from typing import Callable, Iterator, List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.routes.auth import require_current_user
from app.api.routes.feature_gate import require_feature
from app.api.schemas import (
    BackgroundJobInfoResponse,
    DroppedRowResponse,
    FilterConditionRequest,
    FilterPreviewResponse,
    JobStatusResponse,
    StatementAnalysisResponse,
    StatementResponse,
    StatementUploadRequest,
    StatementUploadResponse,
    StatisticsPreviewRequest,
    StatisticsPreviewResponse,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.dto.statement_processing import (
    FilterCondition,
    FilterOperator,
    LogicalOperator,
    RowFilter,
)
from app.domain.models.user import User
from app.logging.utils import log_exception
from app.services.subscription import Feature

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
        current_user: User = Depends(require_current_user),
    ):
        try:
            file_content = await file.read()
            result = internal.statement_analyzer_service.analyze(
                user_id=current_user.id,
                filename=file.filename,
                file_content=file_content,
            )

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

            dropped_rows = [
                DroppedRowResponse(
                    file_row_number=row.file_row_number,
                    date_value=row.date_value,
                    description=row.description,
                    amount=row.amount,
                    reason=row.reason,
                )
                for row in result.dropped_rows
            ]

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
                "dropped_rows": dropped_rows,
                "dropped_rows_count": len(dropped_rows),
            }

            return StatementAnalysisResponse.model_validate(response_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error analyzing file: {str(e)}",
            )

    @router.post("/{uploaded_file_id}/preview-statistics", response_model=StatisticsPreviewResponse)
    async def preview_statistics(
        uploaded_file_id: str,
        preview_request: StatisticsPreviewRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            row_filter = None
            if preview_request.row_filters and preview_request.row_filters.conditions:
                filter_conditions = [
                    FilterCondition(
                        column_name=c.column_name,
                        operator=c.operator,
                        value=c.value,
                        case_sensitive=c.case_sensitive,
                    )
                    for c in preview_request.row_filters.conditions
                ]
                row_filter = RowFilter(
                    conditions=filter_conditions,
                    logical_operator=LogicalOperator(preview_request.row_filters.logical_operator.value),
                )

            result = internal.statement_analyzer_service.preview_statistics(
                uploaded_file_id=uploaded_file_id,
                column_mapping=preview_request.column_mapping,
                header_row_index=preview_request.header_row_index,
                data_start_row_index=preview_request.data_start_row_index,
                row_filter=row_filter,
                account_id=preview_request.account_id,
            )

            filter_preview_response = None
            if result.filter_preview:
                filter_preview_response = FilterPreviewResponse(
                    total_rows=result.filter_preview.total_rows,
                    included_rows=result.filter_preview.included_rows,
                    excluded_rows=result.filter_preview.excluded_rows,
                    included_row_indices=result.filter_preview.included_row_indices,
                    excluded_row_indices=result.filter_preview.excluded_row_indices,
                )

            return StatisticsPreviewResponse(
                total_transactions=result.total_transactions,
                unique_transactions=result.unique_transactions,
                duplicate_transactions=result.duplicate_transactions,
                date_range=result.date_range,
                total_amount=result.total_amount,
                total_debit=result.total_debit,
                total_credit=result.total_credit,
                filter_preview=filter_preview_response,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error previewing statistics: {str(e)}",
            )

    @router.post("/upload", response_model=StatementUploadResponse)
    async def upload_statement(
        upload_data: StatementUploadRequest,
        background_tasks: BackgroundTasks,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            require_feature(internal.subscription_service, current_user.id, Feature.STATEMENT_UPLOAD)

            account = internal.account_service.get_account(UUID(upload_data.account_id), current_user.id)
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {upload_data.account_id} not found",
                )

            result = internal.statement_upload_service.upload_statement(
                user_id=current_user.id,
                upload_data=upload_data,
                background_tasks=background_tasks,
                internal_deps=internal,
            )

            dropped_rows_response = [
                DroppedRowResponse(
                    file_row_number=row.file_row_number,
                    date_value=row.date_value,
                    description=row.description,
                    amount=row.amount,
                    reason=row.reason,
                )
                for row in result.dropped_rows
            ]

            message = (
                f"Successfully processed {result.total_processed} transactions. "
                f"{result.rule_based_matches} matched by rules ({result.match_rate_percentage}%). "
                f"{result.duplicated_transactions} duplicates found."
            )
            if result.dropped_rows:
                message += f" {len(result.dropped_rows)} rows skipped due to invalid dates."

            response = StatementUploadResponse(
                uploaded_file_id=result.uploaded_file_id,
                transactions_saved=result.transactions_saved,
                duplicated_transactions=result.duplicated_transactions,
                success=True,
                message=message,
                total_processed=result.total_processed,
                rule_based_matches=result.rule_based_matches,
                match_rate_percentage=result.match_rate_percentage,
                processing_time_ms=result.processing_time_ms,
                background_job=None,
                dropped_rows=dropped_rows_response,
                dropped_rows_count=len(result.dropped_rows),
            )

            if result.background_job_info:
                response.background_job = BackgroundJobInfoResponse(
                    job_id=str(result.background_job_info.job_id),
                    status=result.background_job_info.status,
                    remaining_transactions=result.background_job_info.remaining_transactions,
                    estimated_completion_seconds=result.background_job_info.estimated_completion_seconds,
                    status_url=result.background_job_info.status_url,
                )

            if result.transactions_saved > 0:
                internal.subscription_service.increment_statement_usage(current_user.id)

            return response

        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error processing statement: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing statement: {str(e)}",
            )

    @router.get("", response_model=List[StatementResponse])
    async def list_statements(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            statements = internal.statement_service.get_all_statements(current_user.id)
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
        current_user: User = Depends(require_current_user),
    ):
        try:
            result = internal.statement_service.delete_statement_with_transactions(statement_id, current_user.id)
            return result
        except ValueError as e:
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
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.get(
        "/categorization-jobs/{job_id}/status",
        response_model=JobStatusResponse,
    )
    async def get_job_status(
        job_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
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
