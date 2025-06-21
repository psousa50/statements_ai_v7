import asyncio
import logging
import time
from typing import Callable, List, Optional
from uuid import UUID

from app.domain.models.counterparty import BatchCounterpartyResult, CounterpartyResult
from app.domain.models.processing import ProcessingProgress
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.categorizers.transaction_counterparty import TransactionCounterparty
from app.ports.repositories.transaction import TransactionRepository

logger = logging.getLogger(__name__)


class TransactionCounterpartyService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        transaction_counterparty: TransactionCounterparty,
    ) -> None:
        self.transaction_repository: TransactionRepository = transaction_repository
        self.transaction_counterparty: TransactionCounterparty = transaction_counterparty

    def process_unprocessed_transactions_detailed(self, batch_size: int = 10) -> BatchCounterpartyResult:
        """Process transactions that don't have counterparty accounts identified"""
        transactions: List[Transaction] = self.transaction_repository.get_transactions_without_counterparty(limit=batch_size)

        if not transactions:
            return BatchCounterpartyResult(results=[], total_processed=0, successful_count=0, failed_count=0)

        counterparty_results: List[CounterpartyResult] = self.transaction_counterparty.identify_counterparty(transactions)

        for result in counterparty_results:
            transaction = next((t for t in transactions if t.id == result.transaction_id), None)
            if transaction:
                transaction.counterparty_account_id = result.counterparty_account_id
                # Note: We don't update categorization_status for counterparty identification
                # since it's a separate concern from categorization
                self.transaction_repository.update(transaction)

        successful_count = sum(1 for result in counterparty_results if result.status == CategorizationStatus.CATEGORIZED)
        failed_count = len(counterparty_results) - successful_count

        return BatchCounterpartyResult(
            results=counterparty_results,
            total_processed=len(counterparty_results),
            successful_count=successful_count,
            failed_count=failed_count,
        )

    async def identify_counterparty_batch_by_ids(
        self,
        transaction_ids: List[UUID],
        progress_callback: Optional[Callable[[ProcessingProgress], None]] = None,
        batch_size: int = 20,
    ) -> dict:
        """
        Identify counterparty accounts for a batch of transactions by their IDs with progress tracking.

        Args:
            transaction_ids: List of transaction UUIDs to process
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
                "successfully_identified": 0,
                "failed_identifications": 0,
                "processing_time_ms": 0,
            }

        logger.info(f"Processing {total_transactions} transactions for AI counterparty identification")

        total_processed = 0
        successful_identifications = 0
        failed_identifications = 0

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
                    phase="AI_COUNTERPARTY_IDENTIFYING",
                )
                progress_callback(progress)

            # Process the batch
            try:
                batch_results = await self._identify_counterparty_batch_by_ids(batch_ids)
                successful_identifications += batch_results["successful"]
                failed_identifications += batch_results["failed"]
                total_processed += len(batch_ids)
            except Exception as e:
                logger.warning(f"Failed to identify counterparties for batch: {e}")
                failed_identifications += len(batch_ids)
                total_processed += len(batch_ids)

            # Small delay between batches to avoid overwhelming the system
            await asyncio.sleep(0.1)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        result = {
            "total_processed": total_processed,
            "successfully_identified": successful_identifications,
            "failed_identifications": failed_identifications,
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"AI counterparty identification completed. "
            f"Processed: {total_processed}, Success: {successful_identifications}, "
            f"Failed: {failed_identifications}, Time: {processing_time_ms}ms"
        )

        return result

    async def _identify_counterparty_batch_by_ids(self, transaction_ids: List[UUID]) -> dict:
        """
        Identify counterparty accounts for a batch of transactions using AI.

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
            # Call the counterparty identifier with the entire batch
            counterparty_results = self.transaction_counterparty.identify_counterparty(transactions)

            successful_count = 0
            failed_count = 0

            # Process results for each transaction
            for i, transaction in enumerate(transactions):
                try:
                    if i < len(counterparty_results):
                        result = counterparty_results[i]

                        if result.status == CategorizationStatus.CATEGORIZED:
                            # Fetch fresh transaction from database to ensure it's attached to session
                            fresh_transaction = self.transaction_repository.get_by_id(transaction.id)
                            if not fresh_transaction:
                                logger.warning(f"Transaction {transaction.id} not found when trying to update")
                                failed_count += 1
                                continue

                            # Update transaction with counterparty result
                            fresh_transaction.counterparty_account_id = result.counterparty_account_id
                            # Note: counterparty_account_id can be None, which is valid

                            # Save to database
                            self.transaction_repository.update(fresh_transaction)

                            successful_count += 1
                            if result.counterparty_account_id:
                                logger.debug(
                                    f"Identified counterparty for transaction {fresh_transaction.id} as {result.counterparty_account_id} "
                                    f"(confidence: {result.confidence:.2f})"
                                    if result.confidence
                                    else f"Identified counterparty for transaction {fresh_transaction.id} as {result.counterparty_account_id}"
                                )
                            else:
                                logger.debug(f"No counterparty identified for transaction {fresh_transaction.id}")
                        else:
                            failed_count += 1
                            logger.warning(
                                f"AI counterparty identification failed for transaction {transaction.id}: {result.error_message}"
                            )
                    else:
                        # No result for this transaction
                        failed_count += 1
                        logger.warning(
                            f"AI counterparty identification failed for transaction {transaction.id}: No result returned"
                        )

                except Exception as e:
                    failed_count += 1
                    logger.warning(f"Failed to process counterparty result for transaction {transaction.id}: {e}")

            # Account for any transactions that weren't found
            failed_count += len(transaction_ids) - len(transactions)

            return {"successful": successful_count, "failed": failed_count}

        except Exception as e:
            logger.error(f"Batch counterparty identification failed for {len(transactions)} transactions: {e}")
            return {"successful": 0, "failed": len(transaction_ids)}

    def _get_transactions_by_ids(self, transaction_ids: List[UUID]) -> List[Transaction]:
        """Get transactions by their IDs"""
        transactions = []
        for transaction_id in transaction_ids:
            transaction = self.transaction_repository.get_by_id(transaction_id)
            if transaction:
                transactions.append(transaction)
        return transactions
