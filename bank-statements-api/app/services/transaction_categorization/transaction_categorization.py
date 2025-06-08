import asyncio
import logging
import time
from typing import Callable, List, Optional
from uuid import UUID

from app.domain.models.categorization import BatchCategorizationResult, CategorizationResult
from app.domain.models.processing import ProcessingProgress
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.domain.models.transaction_categorization import CategorizationSource
from app.ports.categorizers.transaction_categorizer import TransactionCategorizer
from app.ports.repositories.transaction import TransactionRepository
from app.ports.repositories.transaction_categorization import TransactionCategorizationRepository

logger = logging.getLogger(__name__)


class TransactionCategorizationService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        transaction_categorizer: TransactionCategorizer,
        transaction_categorization_repository: TransactionCategorizationRepository,
    ) -> None:
        self.transaction_repository: TransactionRepository = transaction_repository
        self.transaction_categorizer: TransactionCategorizer = transaction_categorizer
        self.transaction_categorization_repository: TransactionCategorizationRepository = transaction_categorization_repository

    def process_uncategorized_transactions_detailed(self, batch_size: int = 10) -> BatchCategorizationResult:
        transactions: List[Transaction] = self.transaction_repository.get_oldest_uncategorized(limit=batch_size)

        if not transactions:
            return BatchCategorizationResult(results=[], total_processed=0, successful_count=0, failed_count=0)

        categorization_results: List[CategorizationResult] = self.transaction_categorizer.categorize(transactions)

        for result in categorization_results:
            transaction = next((t for t in transactions if t.id == result.transaction_id), None)
            if transaction:
                transaction.category_id = result.category_id
                transaction.categorization_status = result.status
                self.transaction_repository.update(transaction)

        successful_count = sum(1 for result in categorization_results if result.status == CategorizationStatus.CATEGORIZED)
        failed_count = len(categorization_results) - successful_count

        return BatchCategorizationResult(
            results=categorization_results,
            total_processed=len(categorization_results),
            successful_count=successful_count,
            failed_count=failed_count,
        )

    async def categorize_batch_by_ids(
        self,
        transaction_ids: List[UUID],
        progress_callback: Optional[Callable[[ProcessingProgress], None]] = None,
        batch_size: int = 20,
    ) -> dict:
        """
        Categorize a batch of transactions by their IDs with progress tracking.

        Args:
            transaction_ids: List of transaction UUIDs to categorize
            progress_callback: Optional callback for progress updates
            batch_size: Number of transactions to process per batch

        Returns:
            Dict with processing results
        """
        start_time = time.time()
        total_transactions = len(transaction_ids)

        if not transaction_ids:
            return {
                "total_processed": 0,
                "successfully_categorized": 0,
                "failed_categorizations": 0,
                "processing_time_ms": 0,
            }

        logger.info(f"Processing {total_transactions} transactions for AI categorization")

        total_processed = 0
        successful_categorizations = 0
        failed_categorizations = 0

        # Process transactions in batches
        batches = [transaction_ids[i : i + batch_size] for i in range(0, len(transaction_ids), batch_size)]

        for batch_idx, batch_ids in enumerate(batches):
            # Update progress if callback provided
            if progress_callback:
                progress = ProcessingProgress(
                    current_batch=batch_idx + 1,
                    total_batches=len(batches),
                    processed_transactions=total_processed,
                    total_transactions=total_transactions,
                    phase="AI_CATEGORIZING",
                )
                progress_callback(progress)

            # Process the batch
            try:
                batch_results = await self._categorize_transaction_batch_by_ids(batch_ids)
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

        result = {
            "total_processed": total_processed,
            "successfully_categorized": successful_categorizations,
            "failed_categorizations": failed_categorizations,
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"AI categorization completed. "
            f"Processed: {total_processed}, Success: {successful_categorizations}, "
            f"Failed: {failed_categorizations}, Time: {processing_time_ms}ms"
        )

        return result

    async def _categorize_transaction_batch_by_ids(self, transaction_ids: List[UUID]) -> dict:
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
            logger.warning(f"Expected {len(transaction_ids)} transactions, but found {len(transactions)}")

        try:
            # Call the categorizer with the entire batch
            categorization_results = self.transaction_categorizer.categorize(transactions)

            successful_count = 0
            failed_count = 0

            # Process results for each transaction
            for i, transaction in enumerate(transactions):
                try:
                    if i < len(categorization_results):
                        result = categorization_results[i]

                        if result.status == CategorizationStatus.CATEGORIZED and result.category_id:
                            # Fetch fresh transaction from database to ensure it's attached to session
                            fresh_transaction = self.transaction_repository.get_by_id(transaction.id)
                            if not fresh_transaction:
                                logger.warning(f"Transaction {transaction.id} not found when trying to update")
                                failed_count += 1
                                continue

                            # Update transaction with categorization result
                            fresh_transaction.category_id = result.category_id
                            fresh_transaction.categorization_status = result.status
                            if result.confidence:
                                fresh_transaction.categorization_confidence = result.confidence

                            # Save to database
                            self.transaction_repository.update(fresh_transaction)

                            # Create categorization rule for future use
                            try:
                                # Check if rule already exists to avoid duplicate key errors
                                existing_rule = self.transaction_categorization_repository.get_rule_by_normalized_description(
                                    fresh_transaction.normalized_description
                                )
                                if not existing_rule:
                                    self.transaction_categorization_repository.create_rule(
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
                            fresh_transaction = self.transaction_repository.get_by_id(transaction.id)
                            if fresh_transaction:
                                # Mark transaction as failed categorization
                                fresh_transaction.categorization_status = CategorizationStatus.FAILURE
                                self.transaction_repository.update(fresh_transaction)
                            failed_count += 1
                            logger.warning(f"AI categorization failed for transaction {transaction.id}: {result.error_message}")
                    else:
                        # No result for this transaction - fetch fresh transaction to ensure session attachment
                        fresh_transaction = self.transaction_repository.get_by_id(transaction.id)
                        if fresh_transaction:
                            fresh_transaction.categorization_status = CategorizationStatus.FAILURE
                            self.transaction_repository.update(fresh_transaction)
                        failed_count += 1
                        logger.warning(f"AI categorization failed for transaction {transaction.id}: No result returned")

                except Exception as e:
                    # Mark transaction as failed categorization - fetch fresh transaction to ensure session attachment
                    fresh_transaction = self.transaction_repository.get_by_id(transaction.id)
                    if fresh_transaction:
                        fresh_transaction.categorization_status = CategorizationStatus.FAILURE
                        self.transaction_repository.update(fresh_transaction)
                    failed_count += 1
                    logger.warning(f"Failed to process categorization result for transaction {transaction.id}: {e}")

            # Account for any transactions that weren't found
            failed_count += len(transaction_ids) - len(transactions)

            return {"successful": successful_count, "failed": failed_count}

        except Exception as e:
            logger.error(f"Batch categorization failed for {len(transactions)} transactions: {e}")
            # Mark all transactions as failed - fetch fresh transactions to ensure session attachment
            for transaction in transactions:
                try:
                    fresh_transaction = self.transaction_repository.get_by_id(transaction.id)
                    if fresh_transaction:
                        fresh_transaction.categorization_status = CategorizationStatus.FAILURE
                        self.transaction_repository.update(fresh_transaction)
                except Exception as update_error:
                    logger.error(f"Failed to mark transaction {transaction.id} as failed: {update_error}")

            return {"successful": 0, "failed": len(transaction_ids)}

    def _get_transactions_by_ids(self, transaction_ids: List[UUID]) -> List[Transaction]:
        """Get transactions by their IDs"""
        transactions = []
        for transaction_id in transaction_ids:
            transaction = self.transaction_repository.get_by_id(transaction_id)
            if transaction:
                transactions.append(transaction)
        return transactions
