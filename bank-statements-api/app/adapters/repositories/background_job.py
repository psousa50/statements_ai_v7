from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.background_job import BackgroundJob, JobStatus, JobType
from app.ports.repositories.background_job import BackgroundJobRepository


class SQLAlchemyBackgroundJobRepository(BackgroundJobRepository):
    """
    SQLAlchemy implementation of the BackgroundJobRepository.
    Adapter in the Hexagonal Architecture pattern.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, job: BackgroundJob) -> BackgroundJob:
        """Create a new background job"""
        self.db_session.add(job)
        self.db_session.commit()
        self.db_session.refresh(job)
        return job

    def get_by_id(self, job_id: UUID) -> Optional[BackgroundJob]:
        """Get a background job by ID"""
        return self.db_session.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()

    def get_all(self) -> List[BackgroundJob]:
        """Get all background jobs"""
        return self.db_session.query(BackgroundJob).order_by(BackgroundJob.created_at.desc()).all()

    def get_by_status(self, status: JobStatus) -> List[BackgroundJob]:
        """Get all jobs with a specific status"""
        return self.db_session.query(BackgroundJob).filter(BackgroundJob.status == status).order_by(BackgroundJob.created_at.desc()).all()

    def get_by_type(self, job_type: JobType) -> List[BackgroundJob]:
        """Get all jobs of a specific type"""
        return self.db_session.query(BackgroundJob).filter(BackgroundJob.job_type == job_type).order_by(BackgroundJob.created_at.desc()).all()

    def get_pending_jobs(self, limit: int = 10) -> List[BackgroundJob]:
        """Get pending jobs ordered by creation time"""
        return (
            self.db_session.query(BackgroundJob)
            .filter(BackgroundJob.status == JobStatus.PENDING)
            .order_by(BackgroundJob.created_at.asc())  # FIFO - oldest first
            .limit(limit)
            .all()
        )

    def claim_single_pending_job(self) -> Optional[BackgroundJob]:
        """
        Atomically claim a single pending job for processing.

        Uses database-level locking with skip_locked to prevent race conditions.
        If another process is already working on the oldest job, skips to the next one.

        Returns:
            The claimed job with status changed to IN_PROGRESS, or None if no jobs available
        """
        # Find and lock the oldest pending job
        job = (
            self.db_session.query(BackgroundJob)
            .filter(BackgroundJob.status == JobStatus.PENDING)
            .order_by(BackgroundJob.created_at.asc())  # FIFO - oldest first
            .with_for_update(skip_locked=True)  # Skip if locked by another process
            .first()
        )

        if job:
            # Atomically mark as started
            job.mark_started()
            self.db_session.commit()
            # Refresh the job object to ensure it stays attached to the session
            self.db_session.refresh(job)

        return job

    def update(self, job: BackgroundJob) -> BackgroundJob:
        """Update a background job"""
        self.db_session.commit()
        self.db_session.refresh(job)
        return job

    def delete(self, job_id: UUID) -> bool:
        """Delete a background job"""
        job = self.get_by_id(job_id)
        if job:
            self.db_session.delete(job)
            self.db_session.commit()
            return True
        return False

    def get_jobs_by_uploaded_file_id(self, uploaded_file_id: UUID) -> List[BackgroundJob]:
        """Get all jobs associated with an uploaded file"""
        return self.db_session.query(BackgroundJob).filter(BackgroundJob.uploaded_file_id == uploaded_file_id).order_by(BackgroundJob.created_at.desc()).all()

    def cleanup_completed_jobs(self, days_old: int = 7) -> int:
        """Clean up completed jobs older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        # Find jobs to delete
        jobs_to_delete = (
            self.db_session.query(BackgroundJob)
            .filter(
                BackgroundJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]),
                BackgroundJob.completed_at < cutoff_date,
            )
            .all()
        )

        # Delete them
        count = len(jobs_to_delete)
        for job in jobs_to_delete:
            self.db_session.delete(job)

        self.db_session.commit()
        return count
