import logging
from uuid import UUID

from app.core.dependencies import InternalDependencies
from app.domain.models.background_job import JobType

logger = logging.getLogger(__name__)


class JobProcessor:
    """
    Background job processor that handles different types of jobs.

    Designed to be safe for concurrent execution - uses atomic job claiming
    to prevent race conditions between multiple processors.
    """

    def __init__(self, internal: InternalDependencies):
        self.internal = internal

    async def process_pending_jobs(self) -> int:
        """
        Process all available pending jobs one at a time.

        Returns:
            Number of jobs processed
        """
        processed_count = 0

        logger.info("Starting job processor...")

        while True:
            # Atomically claim one job
            job = self.internal.background_job_repository.claim_single_pending_job()

            if not job:
                break  # No more jobs available

            # Extract job data immediately to avoid session detachment issues
            job_id = job.id
            job_type = job.job_type
            job_progress = job.progress.copy() if job.progress else {}

            try:
                logger.info(f"Processing job {job_id} (type: {job_type})")
                await self._process_single_job_by_id(job_id, job_type, job_progress)

            except Exception as e:
                logger.error(f"Failed to process job {job_id}: {e}")
                self._mark_job_failed_by_id(job_id, str(e))

            # Always increment the counter - job was processed even if it failed
            processed_count += 1

        logger.info(f"Job processor completed. Processed {processed_count} jobs.")
        return processed_count

    async def _process_single_job_by_id(self, job_id: UUID, job_type: JobType, job_progress: dict) -> None:
        """Process a single background job based on its type using job ID"""
        raise ValueError(f"No job types are supported: {job_type}")

    def _mark_job_failed_by_id(self, job_id: UUID, error_message: str) -> None:
        """Mark a job as failed with error message using job ID"""
        try:
            self.internal.background_job_service.mark_job_failed(job_id, error_message)
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")


# Convenience function for external use
async def process_pending_jobs(internal: InternalDependencies) -> int:
    """
    Convenience function to process pending jobs.

    Can be called from:
    - FastAPI background tasks (upload trigger)
    - Cron jobs
    - Management commands

    Returns:
        Number of jobs processed
    """
    processor = JobProcessor(internal)
    return await processor.process_pending_jobs()
