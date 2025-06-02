import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.adapters.repositories.background_job import SQLAlchemyBackgroundJobRepository
from app.domain.models.background_job import BackgroundJob, JobStatus, JobType


class TestSQLAlchemyBackgroundJobRepository:
    """Unit tests for SQLAlchemyBackgroundJobRepository"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = MagicMock(spec=Session)
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create repository with mock session"""
        return SQLAlchemyBackgroundJobRepository(mock_session)

    @pytest.fixture
    def sample_job(self):
        """Create a sample background job"""
        return BackgroundJob(
            id=uuid.uuid4(),
            job_type=JobType.AI_CATEGORIZATION,
            status=JobStatus.PENDING,
            uploaded_file_id=uuid.uuid4(),
            progress={"total_transactions": 10},
            result={},
            created_at=datetime.now(timezone.utc),
        )

    def test_create_job(self, repository, mock_session, sample_job):
        """Test creating a background job"""
        # Act
        result = repository.create(sample_job)

        # Assert
        mock_session.add.assert_called_once_with(sample_job)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_job)
        assert result == sample_job

    def test_get_by_id_found(self, repository, mock_session, sample_job):
        """Test getting job by ID when found"""
        # Arrange
        job_id = sample_job.id
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = sample_job

        # Act
        result = repository.get_by_id(job_id)

        # Assert
        mock_session.query.assert_called_once_with(BackgroundJob)
        mock_query.filter.assert_called_once()
        assert result == sample_job

    def test_get_by_id_not_found(self, repository, mock_session):
        """Test getting job by ID when not found"""
        # Arrange
        job_id = uuid.uuid4()
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = None

        # Act
        result = repository.get_by_id(job_id)

        # Assert
        mock_session.query.assert_called_once_with(BackgroundJob)
        assert result is None

    def test_get_all(self, repository, mock_session):
        """Test getting all jobs"""
        # Arrange
        jobs = [
            BackgroundJob(id=uuid.uuid4(), job_type=JobType.AI_CATEGORIZATION),
            BackgroundJob(id=uuid.uuid4(), job_type=JobType.AI_CATEGORIZATION),
        ]
        mock_query = mock_session.query.return_value
        mock_query.order_by.return_value.all.return_value = jobs

        # Act
        result = repository.get_all()

        # Assert
        mock_session.query.assert_called_once_with(BackgroundJob)
        mock_query.order_by.assert_called_once()
        assert result == jobs

    def test_get_by_status(self, repository, mock_session):
        """Test getting jobs by status"""
        # Arrange
        status = JobStatus.PENDING
        jobs = [BackgroundJob(id=uuid.uuid4(), status=status)]
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = jobs

        # Act
        result = repository.get_by_status(status)

        # Assert
        mock_session.query.assert_called_once_with(BackgroundJob)
        mock_query.filter.assert_called_once()
        assert result == jobs

    def test_get_by_type(self, repository, mock_session):
        """Test getting jobs by type"""
        # Arrange
        job_type = JobType.AI_CATEGORIZATION
        jobs = [BackgroundJob(id=uuid.uuid4(), job_type=job_type)]
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = jobs

        # Act
        result = repository.get_by_type(job_type)

        # Assert
        mock_session.query.assert_called_once_with(BackgroundJob)
        mock_query.filter.assert_called_once()
        assert result == jobs

    def test_get_pending_jobs(self, repository, mock_session):
        """Test getting pending jobs with limit"""
        # Arrange
        limit = 5
        jobs = [BackgroundJob(id=uuid.uuid4(), status=JobStatus.PENDING)]
        mock_query = mock_session.query.return_value
        mock_filtered = mock_query.filter.return_value
        mock_ordered = mock_filtered.order_by.return_value
        mock_ordered.limit.return_value.all.return_value = jobs

        # Act
        result = repository.get_pending_jobs(limit)

        # Assert
        mock_session.query.assert_called_once_with(BackgroundJob)
        mock_query.filter.assert_called_once()
        mock_filtered.order_by.assert_called_once()
        mock_ordered.limit.assert_called_once_with(limit)
        assert result == jobs

    def test_update_job(self, repository, mock_session, sample_job):
        """Test updating a job"""
        # Act
        result = repository.update(sample_job)

        # Assert
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_job)
        assert result == sample_job

    def test_delete_job_found(self, repository, mock_session, sample_job):
        """Test deleting a job that exists"""
        # Arrange
        job_id = sample_job.id
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = sample_job

        # Act
        result = repository.delete(job_id)

        # Assert
        mock_session.delete.assert_called_once_with(sample_job)
        mock_session.commit.assert_called_once()
        assert result is True

    def test_delete_job_not_found(self, repository, mock_session):
        """Test deleting a job that doesn't exist"""
        # Arrange
        job_id = uuid.uuid4()
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = None

        # Act
        result = repository.delete(job_id)

        # Assert
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
        assert result is False

    def test_get_jobs_by_uploaded_file_id(self, repository, mock_session):
        """Test getting jobs by uploaded file ID"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        jobs = [BackgroundJob(id=uuid.uuid4(), uploaded_file_id=uploaded_file_id)]
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = jobs

        # Act
        result = repository.get_jobs_by_uploaded_file_id(uploaded_file_id)

        # Assert
        mock_session.query.assert_called_once_with(BackgroundJob)
        mock_query.filter.assert_called_once()
        assert result == jobs

    def test_cleanup_completed_jobs(self, repository, mock_session):
        """Test cleaning up old completed jobs"""
        # Arrange
        days_old = 7
        old_jobs = [
            BackgroundJob(id=uuid.uuid4(), status=JobStatus.COMPLETED),
            BackgroundJob(id=uuid.uuid4(), status=JobStatus.FAILED),
        ]
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.all.return_value = old_jobs

        # Act
        result = repository.cleanup_completed_jobs(days_old)

        # Assert
        mock_session.query.assert_called_once_with(BackgroundJob)
        mock_query.filter.assert_called_once()
        assert mock_session.delete.call_count == 2
        mock_session.commit.assert_called_once()
        assert result == 2
