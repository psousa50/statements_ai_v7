import asyncio
import logging
import time
from typing import List
from uuid import UUID

from app.core.dependencies import InternalDependencies
from app.domain.models.background_job import BackgroundJob, JobType
from app.domain.models.categorization import CategorizationStatus
from app.domain.models.processing import ProcessingProgress
from app.domain.models.transaction import Transaction
from app.domain.models.transaction_categorization import CategorizationSource

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

    async def _process_single_job_by_id(
        self, job_id: UUID, job_type: JobType, job_progress: dict
    ) -> None:
        """Process a single background job based on its type using job ID"""

        if job_type == JobType.AI_CATEGORIZATION:
            await self._process_ai_categorization_job_by_id(job_id, job_progress)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

    async def _process_ai_categorization_job_by_id(
        self, job_id: UUID, job_progress: dict
    ) -> None:
        """
        Process an AI categorization job using job ID.

        Retrieves unmatched transactions and runs AI categorization on them.
        """
        start_time = time.time()

        try:
            # Extract transaction IDs from job progress
            unmatched_transaction_ids = job_progress.get(
                "unmatched_transaction_ids", []
            )
            if not unmatched_transaction_ids:
                raise ValueError("No unmatched transaction IDs found in job progress")

            # Convert string IDs back to UUIDs
            transaction_ids = [UUID(tid) for tid in unmatched_transaction_ids]

            # Verify transactions exist (but don't hold onto the objects)
            total_transactions = len(transaction_ids)
            logger.info(
                f"Processing {total_transactions} transactions for AI categorization"
            )

            # Process transactions in batches using IDs
            total_processed = 0
            successful_categorizations = 0
            failed_categorizations = 0

            batch_size = 20  # Process 5 transactions at a time
            batches = [
                transaction_ids[i : i + batch_size]
                for i in range(0, len(transaction_ids), batch_size)
            ]

            for batch_idx, batch_ids in enumerate(batches):
                # Update progress
                progress = ProcessingProgress(
                    current_batch=batch_idx + 1,
                    total_batches=len(batches),
                    processed_transactions=total_processed,
                    total_transactions=total_transactions,
                    phase="AI_CATEGORIZING",
                )
                self.internal.background_job_service.update_job_progress(
                    job_id, progress
                )

                # Process entire batch at once
                try:
                    batch_results = await self._categorize_transaction_batch_by_ids(
                        batch_ids
                    )
                    successful_categorizations += batch_results["successful"]
                    failed_categorizations += batch_results["failed"]
                    total_processed += len(batch_ids)
                except Exception as e:
                    logger.warning(f"Failed to categorize batch: {e}")
                    failed_categorizations += len(batch_ids)
                    total_processed += len(batch_ids)

                # Small delay between batches to avoid overwhelming the system
                await asyncio.sleep(0.1)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Mark job as completed with results
            result = {
                "total_processed": total_processed,
                "successfully_categorized": successful_categorizations,
                "failed_categorizations": failed_categorizations,
                "processing_time_ms": processing_time_ms,
            }

            self.internal.background_job_service.mark_job_completed(job_id, result)

            logger.info(
                f"AI categorization job {job_id} completed. "
                f"Processed: {total_processed}, Success: {successful_categorizations}, "
                f"Failed: {failed_categorizations}, Time: {processing_time_ms}ms"
            )

        except Exception as e:
            logger.error(f"AI categorization job {job_id} failed: {e}")
            raise

    async def _process_single_job(self, job: BackgroundJob) -> None:
        """Process a single background job based on its type (deprecated - use _process_single_job_by_id)"""
        # This method is kept for backwards compatibility but should not be used
        # Extract data immediately to avoid session issues
        job_id = job.id
        job_type = job.job_type
        job_progress = job.progress.copy() if job.progress else {}
        await self._process_single_job_by_id(job_id, job_type, job_progress)

    async def _process_ai_categorization_job(self, job: BackgroundJob) -> None:
        """Process an AI categorization job (deprecated - use _process_ai_categorization_job_by_id)"""
        # This method is kept for backwards compatibility but should not be used
        # Extract data immediately to avoid session issues
        job_id = job.id
        job_progress = job.progress.copy() if job.progress else {}
        await self._process_ai_categorization_job_by_id(job_id, job_progress)

    def _mark_job_failed_by_id(self, job_id: UUID, error_message: str) -> None:
        """Mark a job as failed with error message using job ID"""
        try:
            self.internal.background_job_service.mark_job_failed(job_id, error_message)
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")

    def _mark_job_failed(self, job: BackgroundJob, error_message: str) -> None:
        """Mark a job as failed with error message (deprecated - use _mark_job_failed_by_id)"""
        # This method is kept for backwards compatibility but should not be used
        # Extract job ID immediately to avoid session issues
        job_id = job.id
        self._mark_job_failed_by_id(job_id, error_message)

    async def _categorize_transaction_batch_by_ids(
        self, transaction_ids: List[UUID]
    ) -> dict:
        """
        Categorize a batch of transactions using AI.

        Returns:
            Dict with 'successful' and 'failed' counts
        """
        # Fetch all transactions in the batch
        transactions = self._get_transactions_by_ids(transaction_ids)

        if not transactions:
            logger.warning(f"No transactions found for batch: {transaction_ids}")
            return {"successful": 0, "failed": len(transaction_ids)}

        # If some transactions weren't found, log the discrepancy
        if len(transactions) != len(transaction_ids):
            logger.warning(
                f"Expected {len(transaction_ids)} transactions, but found {len(transactions)}"
            )

        try:
            # Call the categorizer with the entire batch
            categorization_results = self.internal.transaction_categorization_service.transaction_categorizer.categorize(
                transactions
            )

            successful_count = 0
            failed_count = 0

            # Process results for each transaction
            for i, transaction in enumerate(transactions):
                try:
                    if i < len(categorization_results):
                        result = categorization_results[i]

                        if (
                            result.status == CategorizationStatus.CATEGORIZED
                            and result.category_id
                        ):
                            # Fetch fresh transaction from database to ensure it's attached to session
                            fresh_transaction = self.internal.transaction_service.transaction_repository.get_by_id(
                                transaction.id
                            )
                            if not fresh_transaction:
                                logger.warning(
                                    f"Transaction {transaction.id} not found when trying to update"
                                )
                                failed_count += 1
                                continue

                            # Update transaction with categorization result
                            fresh_transaction.category_id = result.category_id
                            fresh_transaction.categorization_status = result.status
                            if result.confidence:
                                fresh_transaction.categorization_confidence = (
                                    result.confidence
                                )

                            # Save to database
                            self.internal.transaction_service.transaction_repository.update(
                                fresh_transaction
                            )

                            # Create categorization rule for future use
                            try:
                                # Check if rule already exists to avoid duplicate key errors
                                existing_rule = self.internal.transaction_categorization_repository.get_rule_by_normalized_description(
                                    fresh_transaction.normalized_description
                                )
                                if not existing_rule:
                                    self.internal.transaction_categorization_repository.create_rule(
                                        normalized_description=fresh_transaction.normalized_description,
                                        category_id=result.category_id,
                                        source=CategorizationSource.AI,
                                    )
                                    logger.debug(
                                        f"Created AI categorization rule: {fresh_transaction.normalized_description} -> {result.category_id}"
                                    )
                                else:
                                    logger.debug(
                                        f"Categorization rule already exists for: {fresh_transaction.normalized_description}"
                                    )
                            except Exception as e:
                                # Don't fail the transaction categorization if rule creation fails
                                logger.warning(
                                    f"Failed to create categorization rule for {fresh_transaction.normalized_description}: {e}"
                                )

                            successful_count += 1
                            logger.debug(
                                f"Categorized transaction {fresh_transaction.id} as {result.category_id} "
                                f"(confidence: {result.confidence:.2f})"
                                if result.confidence
                                else f"Categorized transaction {fresh_transaction.id} as {result.category_id}"
                            )
                        else:
                            # Fetch fresh transaction to ensure it's attached to session
                            fresh_transaction = self.internal.transaction_service.transaction_repository.get_by_id(
                                transaction.id
                            )
                            if fresh_transaction:
                                # Mark transaction as failed categorization
                                fresh_transaction.categorization_status = (
                                    CategorizationStatus.FAILURE
                                )
                                self.internal.transaction_service.transaction_repository.update(
                                    fresh_transaction
                                )
                            failed_count += 1
                            logger.warning(
                                f"AI categorization failed for transaction {transaction.id}: {result.error_message}"
                            )
                    else:
                        # No result for this transaction - fetch fresh transaction to ensure session attachment
                        fresh_transaction = self.internal.transaction_service.transaction_repository.get_by_id(
                            transaction.id
                        )
                        if fresh_transaction:
                            fresh_transaction.categorization_status = (
                                CategorizationStatus.FAILURE
                            )
                            self.internal.transaction_service.transaction_repository.update(
                                fresh_transaction
                            )
                        failed_count += 1
                        logger.warning(
                            f"AI categorization failed for transaction {transaction.id}: No result returned"
                        )

                except Exception as e:
                    # Mark transaction as failed categorization - fetch fresh transaction to ensure session attachment
                    fresh_transaction = self.internal.transaction_service.transaction_repository.get_by_id(
                        transaction.id
                    )
                    if fresh_transaction:
                        fresh_transaction.categorization_status = (
                            CategorizationStatus.FAILURE
                        )
                        self.internal.transaction_service.transaction_repository.update(
                            fresh_transaction
                        )
                    failed_count += 1
                    logger.warning(
                        f"Failed to process categorization result for transaction {transaction.id}: {e}"
                    )

            # Account for any transactions that weren't found
            failed_count += len(transaction_ids) - len(transactions)

            return {"successful": successful_count, "failed": failed_count}

        except Exception as e:
            logger.error(
                f"Batch categorization failed for {len(transactions)} transactions: {e}"
            )
            # Mark all transactions as failed - fetch fresh transactions to ensure session attachment
            for transaction in transactions:
                try:
                    fresh_transaction = self.internal.transaction_service.transaction_repository.get_by_id(
                        transaction.id
                    )
                    if fresh_transaction:
                        fresh_transaction.categorization_status = (
                            CategorizationStatus.FAILURE
                        )
                        self.internal.transaction_service.transaction_repository.update(
                            fresh_transaction
                        )
                except Exception as update_error:
                    logger.error(
                        f"Failed to mark transaction {transaction.id} as failed: {update_error}"
                    )

            return {"successful": 0, "failed": len(transaction_ids)}

    async def _categorize_single_transaction_by_id(self, transaction_id: UUID) -> None:
        """Categorize a single transaction using AI by fetching fresh transaction"""

        # Fetch fresh transaction from database
        transaction = (
            self.internal.transaction_service.transaction_repository.get_by_id(
                transaction_id
            )
        )
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Use the categorizer directly since we have a specific transaction
        categorization_results = self.internal.transaction_categorization_service.transaction_categorizer.categorize(
            [transaction]
        )

        if categorization_results and len(categorization_results) > 0:
            result = categorization_results[0]  # Get the first (and only) result

            if result.status == CategorizationStatus.CATEGORIZED and result.category_id:
                # Update transaction with categorization result
                transaction.category_id = result.category_id
                transaction.categorization_status = result.status
                if result.confidence:
                    transaction.categorization_confidence = result.confidence

                # Save to database
                self.internal.transaction_service.transaction_repository.update(
                    transaction
                )

                # Create categorization rule for future use
                try:
                    # Check if rule already exists to avoid duplicate key errors
                    existing_rule = self.internal.transaction_categorization_repository.get_rule_by_normalized_description(
                        transaction.normalized_description
                    )
                    if not existing_rule:
                        self.internal.transaction_categorization_repository.create_rule(
                            normalized_description=transaction.normalized_description,
                            category_id=result.category_id,
                            source=CategorizationSource.AI,
                        )
                        logger.debug(
                            f"Created AI categorization rule: {transaction.normalized_description} -> {result.category_id}"
                        )
                    else:
                        logger.debug(
                            f"Categorization rule already exists for: {transaction.normalized_description}"
                        )
                except Exception as e:
                    # Don't fail the transaction categorization if rule creation fails
                    logger.warning(
                        f"Failed to create categorization rule for {transaction.normalized_description}: {e}"
                    )

                logger.debug(
                    f"Categorized transaction {transaction.id} as {result.category_id} "
                    f"(confidence: {result.confidence:.2f})"
                    if result.confidence
                    else f"Categorized transaction {transaction.id} as {result.category_id}"
                )
            else:
                logger.warning(
                    f"AI categorization failed for transaction {transaction.id}: {result.error_message}"
                )
                # Mark transaction as failed categorization
                transaction.categorization_status = CategorizationStatus.FAILURE
                self.internal.transaction_service.transaction_repository.update(
                    transaction
                )
                raise ValueError(f"AI categorization failed: {result.error_message}")
        else:
            logger.warning(
                f"AI categorization failed for transaction {transaction.id}: No results returned"
            )
            # Mark transaction as failed categorization
            transaction.categorization_status = CategorizationStatus.FAILURE
            self.internal.transaction_service.transaction_repository.update(transaction)
            raise ValueError("AI categorization returned no results")

    async def _categorize_single_transaction(self, transaction: Transaction) -> None:
        """Categorize a single transaction using AI (deprecated - use _categorize_single_transaction_by_id)"""
        # This method is kept for backwards compatibility but should not be used
        # Use the ID-based method to avoid session issues
        await self._categorize_single_transaction_by_id(transaction.id)

    def _get_transactions_by_ids(
        self, transaction_ids: List[UUID]
    ) -> List[Transaction]:
        """Get transactions by their IDs"""
        transactions = []
        for transaction_id in transaction_ids:
            transaction = (
                self.internal.transaction_service.transaction_repository.get_by_id(
                    transaction_id
                )
            )
            if transaction:
                transactions.append(transaction)
        return transactions


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
