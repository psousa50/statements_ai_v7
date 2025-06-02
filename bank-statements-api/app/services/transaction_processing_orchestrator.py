import logging
import time
from typing import List, Optional
from uuid import UUID

from app.domain.models.processing import BackgroundJobInfo, SyncCategorizationResult
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.repositories.transaction import TransactionRepository
from app.services.background.background_job_service import BackgroundJobService
from app.services.rule_based_categorization import RuleBasedCategorizationService

logger = logging.getLogger(__name__)


class TransactionProcessingOrchestrator:
    """
    Transaction Processing Orchestrator.

    Orchestrates the complete transaction processing workflow:
    1. Immediate rule-based categorization
    2. Queuing background AI categorization for unmatched transactions
    3. Progress tracking and job management

    This provides synchronous results for rule-matched transactions
    while handling complex AI categorization asynchronously.
    """

    def __init__(
        self,
        rule_based_categorization_service: RuleBasedCategorizationService,
        background_job_service: BackgroundJobService,
        transaction_repository: TransactionRepository,
    ):
        self.rule_based_categorization_service = rule_based_categorization_service
        self.background_job_service = background_job_service
        self.transaction_repository = transaction_repository

    def process_transactions(
        self, uploaded_file_id: UUID, transactions: List[Transaction]
    ) -> SyncCategorizationResult:
        """
        Process transactions with orchestration:
        - Immediate rule-based categorization
        - Queue background jobs for unmatched transactions
        - Return comprehensive results
        """
        start_time_ms = int(time.time() * 1000)

        # Handle empty transaction list
        if not transactions:
            return SyncCategorizationResult(
                total_processed=0,
                rule_based_matches=0,
                unmatched_transaction_ids=[],
                processing_time_ms=int(time.time() * 1000) - start_time_ms,
                match_rate_percentage=0.0,
            )

        logger.info(f"Processing {len(transactions)} transactions with orchestrator")

        # Phase 1: Extract and deduplicate normalized descriptions for rule-based categorization
        normalized_descriptions = [t.normalized_description for t in transactions]
        unique_normalized_descriptions = list(
            dict.fromkeys(normalized_descriptions)
        )  # Preserves order, removes duplicates

        logger.debug(
            f"Deduplicated {len(normalized_descriptions)} descriptions to {len(unique_normalized_descriptions)} unique descriptions"
        )

        # Perform synchronous rule-based categorization on unique descriptions
        rule_matches = self.rule_based_categorization_service.categorize_batch(
            unique_normalized_descriptions
        )

        # Apply rule-based categorization results to transactions
        matched_transactions = []
        unmatched_transactions = []

        for transaction in transactions:
            if transaction.normalized_description in rule_matches:
                # Rule match found - categorize transaction
                category_id = rule_matches[transaction.normalized_description]
                transaction.category_id = category_id
                transaction.categorization_status = CategorizationStatus.CATEGORIZED

                # Save transaction to database
                self.transaction_repository.update(transaction)

                matched_transactions.append(transaction)
                logger.debug(
                    f"Rule match: {transaction.normalized_description} -> {category_id}"
                )
            else:
                # No rule match - transaction remains uncategorized
                unmatched_transactions.append(transaction)
                logger.debug(f"No rule match: {transaction.normalized_description}")

        # Calculate metrics
        total_processed = len(transactions)
        rule_based_matches = len(matched_transactions)
        match_rate_percentage = (
            round((rule_based_matches / total_processed) * 100, 1)
            if total_processed > 0
            else 0.0
        )
        unmatched_transaction_ids = [t.id for t in unmatched_transactions]

        # Phase 2: Queue background job for unmatched transactions (if any)
        if unmatched_transactions:
            logger.info(
                f"Queuing background job for {len(unmatched_transactions)} unmatched transactions"
            )
            self.background_job_service.queue_ai_categorization_job(
                uploaded_file_id, unmatched_transaction_ids
            )

        # Calculate final processing time
        processing_time_ms = int(time.time() * 1000) - start_time_ms

        # Create and return comprehensive result
        result = SyncCategorizationResult(
            total_processed=total_processed,
            rule_based_matches=rule_based_matches,
            unmatched_transaction_ids=unmatched_transaction_ids,
            processing_time_ms=processing_time_ms,
            match_rate_percentage=match_rate_percentage,
        )

        logger.info(
            f"Processing complete: {rule_based_matches}/{total_processed} matched by rules "
            f"({match_rate_percentage}%), {len(unmatched_transactions)} queued for AI processing"
        )

        return result

    def get_background_job_info(
        self, job_id: UUID, status_url_template: str
    ) -> Optional[BackgroundJobInfo]:
        """Get background job information for API responses"""
        return self.background_job_service.get_background_job_info(
            job_id, status_url_template
        )
