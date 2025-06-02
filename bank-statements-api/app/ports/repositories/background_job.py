from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.background_job import BackgroundJob, JobStatus, JobType


class BackgroundJobRepository(ABC):
    """
    Port (interface) for background job repository operations.
    Following Hexagonal Architecture pattern.
    """

    @abstractmethod
    def create(self, job: BackgroundJob) -> BackgroundJob:
        """Create a new background job"""
        pass

    @abstractmethod
    def get_by_id(self, job_id: UUID) -> Optional[BackgroundJob]:
        """Get a background job by ID"""
        pass

    @abstractmethod
    def get_all(self) -> List[BackgroundJob]:
        """Get all background jobs"""
        pass

    @abstractmethod
    def get_by_status(self, status: JobStatus) -> List[BackgroundJob]:
        """Get all jobs with a specific status"""
        pass

    @abstractmethod
    def get_by_type(self, job_type: JobType) -> List[BackgroundJob]:
        """Get all jobs of a specific type"""
        pass

    @abstractmethod
    def get_pending_jobs(self, limit: int = 10) -> List[BackgroundJob]:
        """Get pending jobs ordered by creation time"""
        pass

    @abstractmethod
    def claim_single_pending_job(self) -> Optional[BackgroundJob]:
        """
        Atomically claim a single pending job for processing.

        Uses database-level locking to prevent race conditions.
        Returns None if no pending jobs are available.

        Returns:
            The claimed job with status changed to IN_PROGRESS, or None
        """
        pass

    @abstractmethod
    def update(self, job: BackgroundJob) -> BackgroundJob:
        """Update a background job"""
        pass

    @abstractmethod
    def delete(self, job_id: UUID) -> bool:
        """Delete a background job"""
        pass

    @abstractmethod
    def get_jobs_by_uploaded_file_id(
        self, uploaded_file_id: UUID
    ) -> List[BackgroundJob]:
        """Get all jobs associated with an uploaded file"""
        pass

    @abstractmethod
    def cleanup_completed_jobs(self, days_old: int = 7) -> int:
        """Clean up completed jobs older than specified days"""
        pass
