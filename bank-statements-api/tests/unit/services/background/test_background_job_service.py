import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from app.domain.models.background_job import BackgroundJob, JobStatus, JobType
from app.domain.models.processing import BackgroundJobInfo, ProcessingProgress
from app.ports.repositories.background_job import BackgroundJobRepository
from app.services.background.background_job_service import BackgroundJobService


class TestBackgroundJobService:
    """Unit tests for BackgroundJobService"""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing"""
        repository = MagicMock(spec=BackgroundJobRepository)
        return repository

    @pytest.fixture
    def service(self, mock_repository):
        """Create a service with the mock repository"""
        return BackgroundJobService(mock_repository)

    @pytest.fixture
    def sample_job(self):
        """Create a sample background job for testing"""
        job = BackgroundJob(
            id=uuid.uuid4(),
            job_type=JobType.AI_CATEGORIZATION,
            status=JobStatus.PENDING,
            uploaded_file_id=uuid.uuid4(),
            progress={},
            result={},
            created_at=datetime.now(timezone.utc),
        )
        return job

    def test_queue_ai_categorization_job_success(
        self, service, mock_repository, sample_job
    ):
        """Test successfully queuing an AI categorization job"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        unmatched_transaction_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_repository.create.return_value = sample_job

        # Act
        result = service.queue_ai_categorization_job(
            uploaded_file_id, unmatched_transaction_ids
        )

        # Assert
        assert result == sample_job
        mock_repository.create.assert_called_once()
        created_job = mock_repository.create.call_args[0][0]
        assert created_job.job_type == JobType.AI_CATEGORIZATION
        assert created_job.uploaded_file_id == uploaded_file_id
        assert created_job.status == JobStatus.PENDING
        assert "unmatched_transaction_ids" in created_job.progress
        assert created_job.progress["unmatched_transaction_ids"] == [
            str(tid) for tid in unmatched_transaction_ids
        ]

    def test_queue_ai_categorization_job_empty_transaction_ids(
        self, service, mock_repository
    ):
        """Test queuing job with empty transaction IDs raises error"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        unmatched_transaction_ids = []

        # Act & Assert
        with pytest.raises(
            ValueError, match="Cannot queue job with empty transaction list"
        ):
            service.queue_ai_categorization_job(
                uploaded_file_id, unmatched_transaction_ids
            )

        mock_repository.create.assert_not_called()

    def test_get_job_status_found(self, service, mock_repository, sample_job):
        """Test getting job status when job exists"""
        # Arrange
        job_id = sample_job.id
        mock_repository.get_by_id.return_value = sample_job

        # Act
        result = service.get_job_status(job_id)

        # Assert
        assert result == sample_job
        mock_repository.get_by_id.assert_called_once_with(job_id)

    def test_get_job_status_not_found(self, service, mock_repository):
        """Test getting job status when job doesn't exist"""
        # Arrange
        job_id = uuid.uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.get_job_status(job_id)

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(job_id)

    def test_update_job_progress_success(self, service, mock_repository, sample_job):
        """Test updating job progress successfully"""
        # Arrange
        job_id = sample_job.id
        progress = ProcessingProgress(
            current_batch=2,
            total_batches=5,
            processed_transactions=20,
            total_transactions=50,
            phase="AI_CATEGORIZATION",
            estimated_completion_seconds=30,
        )
        mock_repository.get_by_id.return_value = sample_job
        mock_repository.update.return_value = sample_job

        # Act
        result = service.update_job_progress(job_id, progress)

        # Assert
        assert result == sample_job
        mock_repository.get_by_id.assert_called_once_with(job_id)
        mock_repository.update.assert_called_once_with(sample_job)
        # Check that progress was updated
        assert sample_job.progress["current_batch"] == 2
        assert sample_job.progress["total_batches"] == 5
        assert sample_job.progress["processed_transactions"] == 20
        assert sample_job.progress["total_transactions"] == 50
        assert sample_job.progress["phase"] == "AI_CATEGORIZATION"

    def test_update_job_progress_job_not_found(self, service, mock_repository):
        """Test updating progress for non-existent job"""
        # Arrange
        job_id = uuid.uuid4()
        progress = ProcessingProgress(
            current_batch=1,
            total_batches=5,
            processed_transactions=10,
            total_transactions=50,
            phase="AI_CATEGORIZATION",
        )
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.update_job_progress(job_id, progress)

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(job_id)
        mock_repository.update.assert_not_called()

    def test_mark_job_started_success(self, service, mock_repository, sample_job):
        """Test marking job as started"""
        # Arrange
        job_id = sample_job.id
        mock_repository.get_by_id.return_value = sample_job
        mock_repository.update.return_value = sample_job

        # Act
        result = service.mark_job_started(job_id)

        # Assert
        assert result == sample_job
        mock_repository.get_by_id.assert_called_once_with(job_id)
        mock_repository.update.assert_called_once_with(sample_job)
        assert sample_job.status == JobStatus.IN_PROGRESS
        assert sample_job.started_at is not None

    def test_mark_job_completed_success(self, service, mock_repository, sample_job):
        """Test marking job as completed"""
        # Arrange
        job_id = sample_job.id
        result_data = {"ai_categorized": 45, "failed": 5, "new_rules_learned": 12}
        mock_repository.get_by_id.return_value = sample_job
        mock_repository.update.return_value = sample_job

        # Act
        result = service.mark_job_completed(job_id, result_data)

        # Assert
        assert result == sample_job
        mock_repository.get_by_id.assert_called_once_with(job_id)
        mock_repository.update.assert_called_once_with(sample_job)
        assert sample_job.status == JobStatus.COMPLETED
        assert sample_job.completed_at is not None
        assert sample_job.result == result_data

    def test_mark_job_failed_success(self, service, mock_repository, sample_job):
        """Test marking job as failed"""
        # Arrange
        job_id = sample_job.id
        error_message = "AI service unavailable"
        mock_repository.get_by_id.return_value = sample_job
        mock_repository.update.return_value = sample_job

        # Act
        result = service.mark_job_failed(job_id, error_message)

        # Assert
        assert result == sample_job
        mock_repository.get_by_id.assert_called_once_with(job_id)
        mock_repository.update.assert_called_once_with(sample_job)
        assert sample_job.status == JobStatus.FAILED
        assert sample_job.completed_at is not None
        assert sample_job.error_message == error_message

    def test_retry_failed_job_success(self, service, mock_repository):
        """Test retrying a failed job successfully"""
        # Arrange
        job_id = uuid.uuid4()
        failed_job = BackgroundJob(
            id=job_id,
            job_type=JobType.AI_CATEGORIZATION,
            status=JobStatus.FAILED,
            retry_count=1,
            max_retries=3,
        )
        mock_repository.get_by_id.return_value = failed_job
        mock_repository.update.return_value = failed_job

        # Act
        result = service.retry_failed_job(job_id)

        # Assert
        assert result == failed_job
        mock_repository.get_by_id.assert_called_once_with(job_id)
        mock_repository.update.assert_called_once_with(failed_job)
        assert failed_job.retry_count == 2
        assert failed_job.status == JobStatus.PENDING

    def test_retry_failed_job_max_retries_exceeded(self, service, mock_repository):
        """Test retrying job when max retries exceeded"""
        # Arrange
        job_id = uuid.uuid4()
        failed_job = BackgroundJob(
            id=job_id,
            job_type=JobType.AI_CATEGORIZATION,
            status=JobStatus.FAILED,
            retry_count=3,
            max_retries=3,
        )
        mock_repository.get_by_id.return_value = failed_job

        # Act & Assert
        with pytest.raises(ValueError, match="Job has exceeded maximum retry attempts"):
            service.retry_failed_job(job_id)

        mock_repository.get_by_id.assert_called_once_with(job_id)
        mock_repository.update.assert_not_called()

    def test_retry_failed_job_not_failed_status(
        self, service, mock_repository, sample_job
    ):
        """Test retrying job that is not in failed status"""
        # Arrange
        job_id = sample_job.id
        sample_job.status = JobStatus.COMPLETED
        mock_repository.get_by_id.return_value = sample_job

        # Act & Assert
        with pytest.raises(ValueError, match="Only failed jobs can be retried"):
            service.retry_failed_job(job_id)

        mock_repository.get_by_id.assert_called_once_with(job_id)
        mock_repository.update.assert_not_called()

    def test_get_background_job_info(self, service, mock_repository, sample_job):
        """Test getting background job info for API response"""
        # Arrange
        job_id = sample_job.id
        sample_job.progress = {"unmatched_transaction_ids": ["id1", "id2", "id3"]}
        mock_repository.get_by_id.return_value = sample_job

        # Act
        result = service.get_background_job_info(
            job_id, "http://api.com/jobs/{}/status"
        )

        # Assert
        assert isinstance(result, BackgroundJobInfo)
        assert result.job_id == job_id
        assert result.status == sample_job.status
        assert result.remaining_transactions == 3
        assert result.status_url == f"http://api.com/jobs/{job_id}/status"

    def test_get_background_job_info_not_found(self, service, mock_repository):
        """Test getting background job info when job not found"""
        # Arrange
        job_id = uuid.uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.get_background_job_info(
            job_id, "http://api.com/jobs/{}/status"
        )

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(job_id)

    def test_estimate_completion_time(self, service):
        """Test completion time estimation"""
        # Arrange
        remaining_transactions = 50
        avg_processing_time_per_transaction = 0.5  # 500ms per transaction

        # Act
        result = service.estimate_completion_time(
            remaining_transactions, avg_processing_time_per_transaction
        )

        # Assert
        assert result == 25  # 50 * 0.5 = 25 seconds

    def test_estimate_completion_time_zero_transactions(self, service):
        """Test completion time estimation with zero transactions"""
        # Act
        result = service.estimate_completion_time(0, 0.5)

        # Assert
        assert result == 0
