import logging
import time
from typing import List, Optional
from uuid import UUID

from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.processing import BackgroundJobInfo, DTOProcessingResult, SyncCategorizationResult
from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus, Transaction
from app.ports.repositories.transaction import TransactionRepository
from app.services.background.background_job_service import BackgroundJobService
from app.services.rule_based_categorization import RuleBasedCategorizationService
from app.services.rule_based_counterparty import RuleBasedCounterpartyService

logger = logging.getLogger(__name__)


class TransactionProcessingOrchestrator:
    """
    Transaction Processing Orchestrator.

    Orchestrates the complete transaction processing workflow:
    1. Immediate rule-based categorization
    2. Immediate rule-based counterparty identification
    3. Queuing background AI categorization for unmatched transactions
    4. Progress tracking and job management

    This provides synchronous results for rule-matched transactions
    while handling complex AI categorization asynchronously.
    """

    def __init__(
        self,
        rule_based_categorization_service: RuleBasedCategorizationService,
        rule_based_counterparty_service: RuleBasedCounterpartyService,
        background_job_service: BackgroundJobService,
        transaction_repository: TransactionRepository,
    ):
        self.rule_based_categorization_service = rule_based_categorization_service
        self.rule_based_counterparty_service = rule_based_counterparty_service
        self.background_job_service = background_job_service
        self.transaction_repository = transaction_repository

    def process_transactions(self, uploaded_file_id: UUID, transactions: List[Transaction]) -> SyncCategorizationResult:
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
        unique_normalized_descriptions = list(dict.fromkeys(normalized_descriptions))  # Preserves order, removes duplicates

        logger.debug(
            f"Deduplicated {len(normalized_descriptions)} descriptions to {len(unique_normalized_descriptions)} unique descriptions"
        )

        # Perform synchronous rule-based categorization on unique descriptions
        rule_matches = self.rule_based_categorization_service.categorize_batch(unique_normalized_descriptions)

        # Phase 1b: Rule-based counterparty identification
        description_amount_pairs = [(t.normalized_description, t.amount) for t in transactions]
        unique_description_amount_pairs = list(dict.fromkeys(description_amount_pairs))  # Remove duplicates

        counterparty_matches = self.rule_based_counterparty_service.identify_counterparty_batch(unique_description_amount_pairs)

        # Apply rule-based categorization and counterparty results to transactions
        matched_transactions = []
        unmatched_transactions = []

        for transaction in transactions:
            categorization_matched = transaction.normalized_description in rule_matches
            counterparty_matched = transaction.normalized_description in counterparty_matches

            if categorization_matched:
                # Rule match found - categorize transaction
                category_id = rule_matches[transaction.normalized_description]
                transaction.category_id = category_id
                transaction.categorization_status = CategorizationStatus.CATEGORIZED
                logger.debug(f"Categorization rule match: {transaction.normalized_description} -> {category_id}")

            if counterparty_matched:
                # Counterparty rule match found
                counterparty_account_id = counterparty_matches[transaction.normalized_description]
                transaction.counterparty_account_id = counterparty_account_id
                transaction.counterparty_status = CounterpartyStatus.INFERRED
                logger.debug(f"Counterparty rule match: {transaction.normalized_description} -> {counterparty_account_id}")

            # Save transaction to database if any changes were made
            if categorization_matched or counterparty_matched:
                self.transaction_repository.update(transaction)

            if categorization_matched:
                matched_transactions.append(transaction)
            else:
                # No categorization rule match - transaction remains uncategorized
                unmatched_transactions.append(transaction)
                logger.debug(f"No categorization rule match: {transaction.normalized_description}")

        # Calculate metrics
        total_processed = len(transactions)
        rule_based_matches = len(matched_transactions)
        match_rate_percentage = round((rule_based_matches / total_processed) * 100, 1) if total_processed > 0 else 0.0
        unmatched_transaction_ids = [t.id for t in unmatched_transactions]

        # Phase 2: Queue background job for unmatched transactions (if any)
        if unmatched_transactions:
            logger.info(f"Queuing background job for {len(unmatched_transactions)} unmatched transactions")
            self.background_job_service.queue_ai_categorization_job(uploaded_file_id, unmatched_transaction_ids)

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

    def process_transaction_dtos(self, transaction_dtos: List[TransactionDTO], uploaded_file_id: UUID) -> DTOProcessingResult:
        """
        Process transaction DTOs with rule-based categorization.
        DTOs are processed and enriched but not persisted.
        Background jobs are scheduled for unmatched DTOs.
        """
        start_time_ms = int(time.time() * 1000)

        # Handle empty transaction list
        if not transaction_dtos:
            return DTOProcessingResult(
                processed_dtos=[],
                total_processed=0,
                rule_based_matches=0,
                unmatched_dto_count=0,
                processing_time_ms=int(time.time() * 1000) - start_time_ms,
                match_rate_percentage=0.0,
            )

        logger.info(f"Processing {len(transaction_dtos)} transaction DTOs with orchestrator")

        # Phase 1: Extract and deduplicate normalized descriptions for rule-based categorization
        # For DTOs, we need to create normalized descriptions first
        for dto in transaction_dtos:
            # Apply the same normalization logic as entities
            from app.common.text_normalization import normalize_description

            dto.normalized_description = normalize_description(dto.description)

        normalized_descriptions = [dto.normalized_description for dto in transaction_dtos]
        unique_normalized_descriptions = list(dict.fromkeys(normalized_descriptions))  # Preserves order, removes duplicates

        logger.debug(
            f"Deduplicated {len(normalized_descriptions)} descriptions to {len(unique_normalized_descriptions)} unique descriptions"
        )

        # Perform synchronous rule-based categorization on unique descriptions
        rule_matches = self.rule_based_categorization_service.categorize_batch(unique_normalized_descriptions)

        # Phase 1b: Rule-based counterparty identification for DTOs
        description_amount_pairs = [(dto.normalized_description, dto.amount) for dto in transaction_dtos]
        unique_description_amount_pairs = list(dict.fromkeys(description_amount_pairs))  # Remove duplicates

        counterparty_matches = self.rule_based_counterparty_service.identify_counterparty_batch(unique_description_amount_pairs)

        # Apply rule-based categorization and counterparty results to DTOs
        matched_dtos = []
        unmatched_dtos = []

        for dto in transaction_dtos:
            categorization_matched = dto.normalized_description in rule_matches
            counterparty_matched = dto.normalized_description in counterparty_matches

            if categorization_matched:
                # Rule match found - enrich DTO with category
                category_id = rule_matches[dto.normalized_description]
                dto.category_id = category_id
                dto.categorization_status = CategorizationStatus.CATEGORIZED
                logger.debug(f"Categorization rule match: {dto.normalized_description} -> {category_id}")
            else:
                # No categorization rule match - DTO remains uncategorized
                dto.categorization_status = CategorizationStatus.UNCATEGORIZED

            if counterparty_matched:
                # Counterparty rule match found - enrich DTO with counterparty
                counterparty_account_id = counterparty_matches[dto.normalized_description]
                dto.counterparty_account_id = counterparty_account_id
                dto.counterparty_status = CounterpartyStatus.INFERRED
                logger.debug(f"Counterparty rule match: {dto.normalized_description} -> {counterparty_account_id}")
            else:
                # No counterparty rule match
                dto.counterparty_status = CounterpartyStatus.UNPROCESSED

            if categorization_matched:
                matched_dtos.append(dto)
            else:
                unmatched_dtos.append(dto)
                logger.debug(f"No categorization rule match: {dto.normalized_description}")

        # Calculate metrics
        total_processed = len(transaction_dtos)
        rule_based_matches = len(matched_dtos)
        match_rate_percentage = round((rule_based_matches / total_processed) * 100, 1) if total_processed > 0 else 0.0

        # Phase 2: Queue background job for unmatched DTOs (if any)
        # Note: We'll need to schedule this for after persistence
        if unmatched_dtos:
            logger.info(f"Will queue background job for {len(unmatched_dtos)} unmatched DTOs after persistence")
            # We can't schedule the job yet because DTOs don't have IDs
            # The job will be scheduled after persistence in the service

        # Calculate final processing time
        processing_time_ms = int(time.time() * 1000) - start_time_ms

        # Create and return comprehensive result
        result = DTOProcessingResult(
            processed_dtos=transaction_dtos,  # All DTOs, both matched and unmatched
            total_processed=total_processed,
            rule_based_matches=rule_based_matches,
            unmatched_dto_count=len(unmatched_dtos),
            processing_time_ms=processing_time_ms,
            match_rate_percentage=match_rate_percentage,
        )

        logger.info(
            f"DTO processing complete: {rule_based_matches}/{total_processed} matched by rules "
            f"({match_rate_percentage}%), {len(unmatched_dtos)} will need AI processing"
        )

        return result

    def get_background_job_info(self, job_id: UUID, status_url_template: str) -> Optional[BackgroundJobInfo]:
        """Get background job information for API responses"""
        return self.background_job_service.get_background_job_info(job_id, status_url_template)
