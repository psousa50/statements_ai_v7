import logging
from uuid import UUID

from app.core.dependencies import InternalDependencies
from app.domain.models.background_job import BackgroundJob, JobType

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

        if job_type == JobType.AI_CATEGORIZATION:
            await self._process_ai_categorization_job_by_id(job_id, job_progress)
        elif job_type == JobType.AI_COUNTERPARTY_IDENTIFICATION:
            await self._process_ai_counterparty_identification_job_by_id(job_id, job_progress)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

    async def _process_ai_categorization_job_by_id(self, job_id: UUID, job_progress: dict) -> None:
        """
        Process an AI categorization job using job ID.

        Delegates to TransactionCategorizationService for actual categorization work.
        """
        try:
            # Extract transaction IDs from job progress
            unmatched_transaction_ids = job_progress.get("unmatched_transaction_ids", [])
            if not unmatched_transaction_ids:
                raise ValueError("No unmatched transaction IDs found in job progress")

            # Convert string IDs back to UUIDs
            transaction_ids = [UUID(tid) for tid in unmatched_transaction_ids]

            # Delegate to the specialized categorization service
            result = await self.internal.transaction_categorization_service.categorize_batch_by_ids(
                transaction_ids,
                progress_callback=lambda progress: self.internal.background_job_service.update_job_progress(job_id, progress),
                batch_size=20,
            )

            # Mark job as completed with results
            self.internal.background_job_service.mark_job_completed(job_id, result)

            logger.info(
                f"AI categorization job {job_id} completed. "
                f"Processed: {result['total_processed']}, Success: {result['successfully_categorized']}, "
                f"Failed: {result['failed_categorizations']}, Time: {result['processing_time_ms']}ms"
            )

        except Exception as e:
            logger.error(f"AI categorization job {job_id} failed: {e}")
            raise

    async def _process_ai_counterparty_identification_job_by_id(self, job_id: UUID, job_progress: dict) -> None:
        """
        Process an AI counterparty identification job using job ID.

        Delegates to TransactionCounterpartyService for actual counterparty identification work.
        """
        try:
            # Extract transaction IDs from job progress
            unprocessed_transaction_ids = job_progress.get("unprocessed_transaction_ids", [])
            if not unprocessed_transaction_ids:
                raise ValueError("No unprocessed transaction IDs found in job progress")

            # Convert string IDs back to UUIDs
            transaction_ids = [UUID(tid) for tid in unprocessed_transaction_ids]

            # Delegate to the specialized counterparty identification service
            result = await self.internal.transaction_counterparty_service.identify_counterparty_batch_by_ids(
                transaction_ids,
                progress_callback=lambda progress: self.internal.background_job_service.update_job_progress(job_id, progress),
                batch_size=20,
            )

            # Mark job as completed with results
            self.internal.background_job_service.mark_job_completed(job_id, result)

            logger.info(
                f"AI counterparty identification job {job_id} completed. "
                f"Processed: {result['total_processed']}, Success: {result['successfully_identified']}, "
                f"Failed: {result['failed_identifications']}, Time: {result['processing_time_ms']}ms"
            )

        except Exception as e:
            logger.error(f"AI counterparty identification job {job_id} failed: {e}")
            raise

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
