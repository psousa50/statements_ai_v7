import logging
import time
from typing import List

from app.common.text_normalization import normalize_description
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus
from app.services.rule_based_categorization import RuleBasedCategorizationService
from app.services.rule_based_counterparty import RuleBasedCounterpartyService

logger = logging.getLogger(__name__)


class EnhancementResult:
    """Result of transaction enhancement processing"""

    def __init__(
        self,
        enhanced_dtos: List[TransactionDTO],
        total_processed: int,
        rule_based_matches: int,
        match_rate_percentage: float,
        processing_time_ms: int,
        has_unmatched: bool,
    ):
        self.enhanced_dtos = enhanced_dtos
        self.total_processed = total_processed
        self.rule_based_matches = rule_based_matches
        self.match_rate_percentage = match_rate_percentage
        self.processing_time_ms = processing_time_ms
        self.has_unmatched = has_unmatched


class TransactionRuleEnhancementService:
    """
    Pure transaction enhancement service for rule-based processing.

    Applies rule-based categorization and counterparty identification
    to transaction DTOs without any database operations or side effects.
    """

    def __init__(
        self,
        rule_based_categorization_service: RuleBasedCategorizationService,
        rule_based_counterparty_service: RuleBasedCounterpartyService,
    ):
        self.rule_based_categorization_service = rule_based_categorization_service
        self.rule_based_counterparty_service = rule_based_counterparty_service

    def enhance_transactions(self, transaction_dtos: List[TransactionDTO]) -> EnhancementResult:
        """
        Enhance transaction DTOs with rule-based categorization and counterparty identification.

        This is a pure function with no side effects - it only enriches the DTOs
        and returns metrics about the processing.
        """
        start_time_ms = int(time.time() * 1000)

        # Handle empty transaction list
        if not transaction_dtos:
            return EnhancementResult(
                enhanced_dtos=[],
                total_processed=0,
                rule_based_matches=0,
                match_rate_percentage=0.0,
                processing_time_ms=int(time.time() * 1000) - start_time_ms,
                has_unmatched=False,
            )

        logger.info(f"Enhancing {len(transaction_dtos)} transaction DTOs")

        # Step 1: Add normalized descriptions to DTOs
        for dto in transaction_dtos:
            dto.normalized_description = normalize_description(dto.description)

        # Step 2: Extract unique normalized descriptions for efficient batch processing
        # Filter out None values from normalized descriptions
        normalized_descriptions = [dto.normalized_description for dto in transaction_dtos if dto.normalized_description]
        unique_normalized_descriptions = list(dict.fromkeys(normalized_descriptions))

        logger.debug(
            f"Deduplicated {len(normalized_descriptions)} descriptions to "
            f"{len(unique_normalized_descriptions)} unique descriptions"
        )

        # Step 3: Perform rule-based categorization on unique descriptions
        rule_matches = self.rule_based_categorization_service.categorize_batch(unique_normalized_descriptions)

        # Step 4: Perform rule-based counterparty identification
        # Filter out DTOs with None normalized_description and convert amount to Decimal
        from decimal import Decimal

        description_amount_pairs = [
            (dto.normalized_description, Decimal(str(dto.amount))) for dto in transaction_dtos if dto.normalized_description
        ]
        unique_description_amount_pairs = list(dict.fromkeys(description_amount_pairs))

        counterparty_matches = self.rule_based_counterparty_service.identify_counterparty_batch(unique_description_amount_pairs)

        # Step 5: Apply enhancements to DTOs
        matched_count = 0
        unmatched_count = 0

        for dto in transaction_dtos:
            # Only process DTOs with normalized descriptions
            if dto.normalized_description:
                categorization_matched = dto.normalized_description in rule_matches
                counterparty_matched = dto.normalized_description in counterparty_matches

                # Apply categorization enhancement
                if categorization_matched:
                    category_id = rule_matches[dto.normalized_description]
                    dto.category_id = category_id
                    dto.categorization_status = CategorizationStatus.CATEGORIZED
                    matched_count += 1
                    logger.debug(f"Categorization rule match: {dto.normalized_description} -> {category_id}")
                else:
                    dto.categorization_status = CategorizationStatus.UNCATEGORIZED
                    unmatched_count += 1
                    logger.debug(f"No categorization rule match: {dto.normalized_description}")

                # Apply counterparty enhancement
                if counterparty_matched:
                    counterparty_account_id = counterparty_matches[dto.normalized_description]
                    dto.counterparty_account_id = counterparty_account_id
                    dto.counterparty_status = CounterpartyStatus.INFERRED
                    logger.debug(f"Counterparty rule match: {dto.normalized_description} -> {counterparty_account_id}")
                else:
                    dto.counterparty_status = CounterpartyStatus.UNPROCESSED
            else:
                # Handle DTOs without normalized descriptions
                dto.categorization_status = CategorizationStatus.UNCATEGORIZED
                dto.counterparty_status = CounterpartyStatus.UNPROCESSED
                unmatched_count += 1

        # Step 6: Calculate metrics
        total_processed = len(transaction_dtos)
        match_rate_percentage = round((matched_count / total_processed) * 100, 1) if total_processed > 0 else 0.0
        processing_time_ms = int(time.time() * 1000) - start_time_ms

        result = EnhancementResult(
            enhanced_dtos=transaction_dtos,
            total_processed=total_processed,
            rule_based_matches=matched_count,
            match_rate_percentage=match_rate_percentage,
            processing_time_ms=processing_time_ms,
            has_unmatched=unmatched_count > 0,
        )

        logger.info(
            f"Enhancement complete: {matched_count}/{total_processed} matched by rules "
            f"({match_rate_percentage}%), {unmatched_count} unmatched"
        )

        return result
