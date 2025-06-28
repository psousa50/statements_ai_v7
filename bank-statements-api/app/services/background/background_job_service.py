import logging
from typing import Optional
from uuid import UUID

from app.domain.models.background_job import BackgroundJob, JobStatus
from app.domain.models.processing import BackgroundJobInfo, ProcessingProgress
from app.ports.repositories.background_job import BackgroundJobRepository

logger = logging.getLogger(__name__)


class BackgroundJobService:
    """
    Service for managing background jobs.

    Handles queuing, status tracking, and lifecycle management of background jobs.
    """

    def __init__(self, repository: BackgroundJobRepository):
        self.repository = repository

    def get_job_status(self, job_id: UUID) -> Optional[BackgroundJob]:
        """Get job status by ID"""
        return self.repository.get_by_id(job_id)

    def update_job_progress(self, job_id: UUID, progress: ProcessingProgress) -> Optional[BackgroundJob]:
        """Update job progress"""
        job = self.repository.get_by_id(job_id)
        if not job:
            return None

        # Update progress data
        job.progress.update(
            {
                "current_batch": progress.current_batch,
                "total_batches": progress.total_batches,
                "processed_transactions": progress.processed_transactions,
                "total_transactions": progress.total_transactions,
                "phase": progress.phase,
            }
        )

        if progress.estimated_completion_seconds:
            job.progress["estimated_completion_seconds"] = progress.estimated_completion_seconds

        # Save updated job
        updated_job = self.repository.update(job)
        logger.debug(f"Updated progress for job {job_id}: {progress.percentage:.1f}% complete")

        return updated_job

    def mark_job_started(self, job_id: UUID) -> Optional[BackgroundJob]:
        """Mark job as started"""
        job = self.repository.get_by_id(job_id)
        if not job:
            return None

        # Use the model's built-in method
        job.mark_started()

        # Save updated job
        updated_job = self.repository.update(job)
        logger.info(f"Marked job {job_id} as started")

        return updated_job

    def mark_job_completed(self, job_id: UUID, result: dict = None) -> Optional[BackgroundJob]:
        """Mark job as completed with results"""
        job = self.repository.get_by_id(job_id)
        if not job:
            return None

        # Use the model's built-in method
        job.mark_completed(result)

        # Save updated job
        updated_job = self.repository.update(job)
        logger.info(f"Marked job {job_id} as completed")

        return updated_job

    def mark_job_failed(self, job_id: UUID, error_message: str = None) -> Optional[BackgroundJob]:
        """Mark job as failed with error message"""
        job = self.repository.get_by_id(job_id)
        if not job:
            return None

        # Use the model's built-in method
        job.mark_failed(error_message)

        # Save updated job
        updated_job = self.repository.update(job)
        logger.warning(f"Marked job {job_id} as failed: {error_message}")

        return updated_job

    def retry_failed_job(self, job_id: UUID) -> BackgroundJob:
        """Retry a failed job"""
        job = self.repository.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status != JobStatus.FAILED:
            raise ValueError("Only failed jobs can be retried")

        if not job.can_retry:
            raise ValueError("Job has exceeded maximum retry attempts")

        # Use the model's built-in method
        job.increment_retry()

        # Save updated job
        updated_job = self.repository.update(job)
        logger.info(f"Retrying job {job_id} (attempt {updated_job.retry_count}/{updated_job.max_retries})")

        return updated_job

    def get_background_job_info(self, job_id: UUID, status_url_template: str) -> Optional[BackgroundJobInfo]:
        """Get background job info for API responses"""
        job = self.repository.get_by_id(job_id)
        if not job:
            return None

        # Calculate remaining transactions
        unmatched_ids = job.progress.get("unmatched_transaction_ids", [])
        remaining_transactions = len(unmatched_ids)

        # Build status URL
        status_url = status_url_template.format(job_id) if "{}" in status_url_template else None

        # Estimate completion time if job is in progress
        estimated_completion_seconds = None
        if job.status == JobStatus.IN_PROGRESS:
            processed = job.progress.get("processed_transactions", 0)
            total = job.progress.get("total_transactions", 0)
            if total > processed:
                # Simple estimation: assume 0.5 seconds per transaction
                estimated_completion_seconds = self.estimate_completion_time(total - processed, 0.5)

        return BackgroundJobInfo(
            job_id=job_id,
            status=job.status,
            remaining_transactions=remaining_transactions,
            estimated_completion_seconds=estimated_completion_seconds,
            status_url=status_url,
        )

    def estimate_completion_time(
        self,
        remaining_transactions: int,
        avg_processing_time_per_transaction: float,
    ) -> int:
        """Estimate completion time in seconds"""
        if remaining_transactions <= 0:
            return 0

        return int(remaining_transactions * avg_processing_time_per_transaction)

    def get_job_status_for_api(self, job_id: UUID) -> Optional[dict]:
        """Get detailed job status information formatted for API responses"""
        job = self.repository.get_by_id(job_id)
        if not job:
            return None

        # Extract progress information
        total_transactions = job.progress.get("total_transactions", 0)
        processed_transactions = job.progress.get("processed_transactions", 0)
        remaining_transactions = total_transactions - processed_transactions
        completion_percentage = (processed_transactions / total_transactions * 100.0) if total_transactions > 0 else 0.0

        # Estimate completion time if job is in progress
        estimated_completion_seconds = None
        if job.status == JobStatus.IN_PROGRESS and remaining_transactions > 0:
            estimated_completion_seconds = self.estimate_completion_time(remaining_transactions, 0.5)

        # Build progress object
        progress_data = {
            "total_transactions": total_transactions,
            "processed_transactions": processed_transactions,
            "remaining_transactions": remaining_transactions,
            "completion_percentage": round(completion_percentage, 1),
            "estimated_completion_seconds": estimated_completion_seconds,
        }

        # Build result object if job is completed
        result_data = None
        if job.status == JobStatus.COMPLETED and job.result:
            result_data = {
                "total_processed": job.result.get("total_processed", 0),
                "successfully_categorized": job.result.get("successfully_categorized", 0),
                "failed_categorizations": job.result.get("failed_categorizations", 0),
                "processing_time_ms": job.result.get("processing_time_ms", 0),
            }

        return {
            "job_id": job.id,
            "status": job.status,
            "progress": progress_data,
            "result": result_data,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }
