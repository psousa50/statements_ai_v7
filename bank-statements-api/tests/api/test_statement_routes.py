from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from app.api.schemas import JobStatusResponse, StatementAnalysisResponse, StatementUploadRequest, StatementUploadResponse
from app.domain.dto.statement_processing import AnalysisResultDTO
from app.domain.models.background_job import JobStatus
from app.domain.models.processing import BackgroundJobInfo
from tests.api.helpers import build_client, mocked_dependencies


class TestStatementRoutes:
    def test_analyze_statement_success(self):
        file_content = b"Date,Amount,Description\n2023-01-01,100.00,Test"
        uploaded_file_id = str(uuid4())

        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)

        internal_dependencies.statement_analyzer_service.analyze.return_value = AnalysisResultDTO(
            uploaded_file_id=uploaded_file_id,
            file_type="CSV",
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
            sample_data=[["2023-01-01", 100.00, "Test"]],
        )

        response = client.post(
            "/api/v1/statements/analyze",
            files={"file": ("test.csv", BytesIO(file_content), "text/csv")},
        )

        analysis_result = StatementAnalysisResponse.model_validate(response.json())

        assert response.status_code == 200
        assert analysis_result.uploaded_file_id == uploaded_file_id
        assert analysis_result.file_type == "CSV"
        assert analysis_result.column_mapping["date"] == "Date"

        internal_dependencies.statement_analyzer_service.analyze.assert_called_once()
        args, kwargs = internal_dependencies.statement_analyzer_service.analyze.call_args
        assert kwargs["filename"] == "test.csv"
        assert kwargs["file_content"] == file_content

    def test_analyze_statement_error(self):
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        internal_dependencies.statement_analyzer_service.analyze.side_effect = Exception("Test error")

        response = client.post(
            "/api/v1/statements/analyze",
            files={"file": ("test.csv", BytesIO(b"test"), "text/csv")},
        )

        assert response.status_code == 400
        assert "Test error" in response.json()["detail"]

    def test_upload_statement_success(self):
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        uploaded_file_id = str(uuid4())
        source_id = uuid4()

        # Mock the new upload service
        from app.services.statement_processing.statement_upload import StatementUploadResult

        upload_result = StatementUploadResult(
            uploaded_file_id=uploaded_file_id,
            transactions_saved=10,
            total_processed=10,
            rule_based_matches=10,
            match_rate_percentage=100.0,
            processing_time_ms=150,
            background_job_info=None,
        )
        internal_dependencies.statement_upload_service.upload_and_process.return_value = upload_result

        request_data = StatementUploadRequest(
            uploaded_file_id=uploaded_file_id,
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
            source_id=str(source_id),
        )

        response = client.post("/api/v1/statements/upload", json=jsonable_encoder(request_data))

        persistence_result = StatementUploadResponse.model_validate(response.json())

        assert response.status_code == 200
        assert persistence_result.uploaded_file_id == uploaded_file_id
        assert persistence_result.transactions_saved == 10
        assert persistence_result.success is True
        assert persistence_result.total_processed == 10
        assert persistence_result.rule_based_matches == 10
        assert persistence_result.match_rate_percentage == 100.0
        assert persistence_result.processing_time_ms == 150
        assert persistence_result.background_job is None

        # Verify the service was called with the correct request
        call_args = internal_dependencies.statement_upload_service.upload_and_process.call_args
        assert call_args[0][0] == request_data  # First positional arg should be request_data
        assert "background_tasks" in call_args[1]  # Should have background_tasks kwarg
        assert "internal_deps" in call_args[1]  # Should have internal_deps kwarg

    def test_upload_statement_error(self):
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)

        # Mock service failure
        internal_dependencies.statement_upload_service.upload_and_process.side_effect = Exception("Test error")

        request_data = StatementUploadRequest(
            uploaded_file_id=str(uuid4()),
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
            source_id=str(uuid4()),
        )

        response = client.post("/api/v1/statements/upload", json=jsonable_encoder(request_data))

        assert response.status_code == 400
        assert "Test error" in response.json()["detail"]

    def test_upload_with_background_job(self):
        """Test upload when some transactions need background processing"""
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        uploaded_file_id = str(uuid4())
        source_id = uuid4()
        job_id = uuid4()

        # Mock background job info
        background_job_info = BackgroundJobInfo(
            job_id=job_id,
            status=JobStatus.PENDING,
            remaining_transactions=3,
            estimated_completion_seconds=45,
            status_url=f"/api/v1/transactions/categorization-jobs/{job_id}/status",
        )

        # Mock the new upload service with background job
        from app.services.statement_processing.statement_upload import StatementUploadResult

        upload_result = StatementUploadResult(
            uploaded_file_id=uploaded_file_id,
            transactions_saved=10,
            total_processed=10,
            rule_based_matches=7,
            match_rate_percentage=70.0,
            processing_time_ms=250,
            background_job_info=background_job_info,
        )
        internal_dependencies.statement_upload_service.upload_and_process.return_value = upload_result

        # Mock background job repository to prevent hanging when process_pending_jobs is called
        internal_dependencies.background_job_repository.claim_single_pending_job.return_value = None

        request_data = StatementUploadRequest(
            uploaded_file_id=uploaded_file_id,
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
            source_id=str(source_id),
        )

        response = client.post("/api/v1/statements/upload", json=jsonable_encoder(request_data))

        upload_result = StatementUploadResponse.model_validate(response.json())

        assert response.status_code == 200
        assert upload_result.uploaded_file_id == uploaded_file_id
        assert upload_result.transactions_saved == 10
        assert upload_result.success is True
        assert upload_result.total_processed == 10
        assert upload_result.rule_based_matches == 7
        assert upload_result.match_rate_percentage == 70.0
        assert upload_result.processing_time_ms == 250

        # Verify background job info
        assert upload_result.background_job is not None
        assert upload_result.background_job.job_id == job_id
        assert upload_result.background_job.status == JobStatus.PENDING
        assert upload_result.background_job.remaining_transactions == 3
        assert upload_result.background_job.estimated_completion_seconds == 45

    def test_upload_orchestrator_error(self):
        """Test upload when service fails"""
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        uploaded_file_id = str(uuid4())
        source_id = uuid4()

        # Mock service failure
        internal_dependencies.statement_upload_service.upload_and_process.side_effect = Exception("Service failed")

        request_data = StatementUploadRequest(
            uploaded_file_id=uploaded_file_id,
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
            source_id=str(source_id),
        )

        response = client.post("/api/v1/statements/upload", json=jsonable_encoder(request_data))

        assert response.status_code == 400
        assert "Service failed" in response.json()["detail"]


class TestJobStatusRoutes:
    """Tests for job status endpoints"""

    def test_job_status_pending(self):
        """Test job status endpoint for pending job"""
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        job_id = uuid4()

        # Mock background job service
        job_status_response = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "progress": {
                "total_transactions": 5,
                "processed_transactions": 0,
                "remaining_transactions": 5,
                "completion_percentage": 0.0,
                "estimated_completion_seconds": 60,
            },
            "result": None,
            "error_message": None,
            "created_at": datetime.now(timezone.utc),
            "started_at": None,
            "completed_at": None,
        }
        internal_dependencies.background_job_service.get_job_status_for_api.return_value = job_status_response

        response = client.get(f"/api/v1/transactions/categorization-jobs/{job_id}/status")

        status_result = JobStatusResponse.model_validate(response.json())

        assert response.status_code == 200
        assert status_result.job_id == job_id
        assert status_result.status == JobStatus.PENDING
        assert status_result.progress is not None
        assert status_result.progress.total_transactions == 5
        assert status_result.progress.remaining_transactions == 5
        assert status_result.result is None

    def test_job_status_completed(self):
        """Test job status endpoint for completed job"""
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        job_id = uuid4()

        # Mock background job service
        job_status_response = {
            "job_id": job_id,
            "status": JobStatus.COMPLETED,
            "progress": {
                "total_transactions": 5,
                "processed_transactions": 5,
                "remaining_transactions": 0,
                "completion_percentage": 100.0,
                "estimated_completion_seconds": 0,
            },
            "result": {
                "total_processed": 5,
                "successfully_categorized": 4,
                "failed_categorizations": 1,
                "processing_time_ms": 3500,
            },
            "error_message": None,
            "created_at": datetime.now(timezone.utc),
            "started_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
        }
        internal_dependencies.background_job_service.get_job_status_for_api.return_value = job_status_response

        response = client.get(f"/api/v1/transactions/categorization-jobs/{job_id}/status")

        status_result = JobStatusResponse.model_validate(response.json())

        assert response.status_code == 200
        assert status_result.job_id == job_id
        assert status_result.status == JobStatus.COMPLETED
        assert status_result.progress is not None
        assert status_result.progress.completion_percentage == 100.0
        assert status_result.result is not None
        assert status_result.result.total_processed == 5
        assert status_result.result.successfully_categorized == 4

    def test_job_status_not_found(self):
        """Test job status endpoint when job doesn't exist"""
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        job_id = uuid4()

        # Mock background job service returning None
        internal_dependencies.background_job_service.get_job_status_for_api.return_value = None

        response = client.get(f"/api/v1/transactions/categorization-jobs/{job_id}/status")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
