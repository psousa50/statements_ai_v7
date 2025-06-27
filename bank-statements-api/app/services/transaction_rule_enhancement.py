import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import uuid4

from app.common.text_normalization import normalize_description
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.enhancement_rule import EnhancementRule
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.services.transaction_enhancement import TransactionEnhancer

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
    Transaction enhancement service using enhancement rules.

    Applies enhancement rules to transaction DTOs and creates new rules
    for unmatched transactions to enable learning.
    """

    def __init__(
        self,
        transaction_enhancer: TransactionEnhancer,
        enhancement_rule_repository: EnhancementRuleRepository,
    ):
        self.transaction_enhancer = transaction_enhancer
        self.enhancement_rule_repository = enhancement_rule_repository

    def enhance_transactions(self, transaction_dtos: List[TransactionDTO]) -> EnhancementResult:
        """
        Enhance transaction DTOs using enhancement rules and create new rules for unmatched transactions.
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

        # Step 1: Normalize descriptions and convert DTOs to Transaction entities
        transactions = []
        for dto in transaction_dtos:
            dto.normalized_description = normalize_description(dto.description)

            # Convert DTO to Transaction entity for processing
            transaction = self._dto_to_transaction(dto)
            transactions.append(transaction)

        # Step 2: Get all enhancement rules from repository
        rules = self.enhancement_rule_repository.get_all()
        logger.debug(f"Retrieved {len(rules)} enhancement rules")

        # Step 3: Apply enhancement rules using TransactionEnhancer
        enhanced_transactions = self.transaction_enhancer.apply_rules(transactions, rules)

        # Step 4: Convert back to DTOs and calculate metrics
        matched_count = 0
        unmatched_transactions = []

        for i, transaction in enumerate(enhanced_transactions):
            dto = transaction_dtos[i]

            # Copy enhancements back to DTO
            dto.category_id = transaction.category_id
            dto.categorization_status = transaction.categorization_status
            dto.counterparty_account_id = transaction.counterparty_account_id

            # Count matches (any enhancement applied)
            if transaction.category_id or transaction.counterparty_account_id:
                matched_count += 1
            else:
                # Track unmatched transactions for rule creation
                unmatched_transactions.append(transaction)

        # Step 5: Create enhancement rules for unique unmatched normalized descriptions
        unique_normalized_descriptions = {t.normalized_description for t in unmatched_transactions if t.normalized_description}
        for normalized_description in unique_normalized_descriptions:
            self._create_unmatched_rule(normalized_description)

        # Step 6: Calculate metrics
        total_processed = len(transaction_dtos)
        match_rate_percentage = round((matched_count / total_processed) * 100, 1) if total_processed > 0 else 0.0
        processing_time_ms = int(time.time() * 1000) - start_time_ms
        has_unmatched = len(unmatched_transactions) > 0

        result = EnhancementResult(
            enhanced_dtos=transaction_dtos,
            total_processed=total_processed,
            rule_based_matches=matched_count,
            match_rate_percentage=match_rate_percentage,
            processing_time_ms=processing_time_ms,
            has_unmatched=has_unmatched,
        )

        logger.info(
            f"Enhancement complete: {matched_count}/{total_processed} matched by rules "
            f"({match_rate_percentage}%), {len(unmatched_transactions)} unmatched rules created"
        )

        return result

    def _dto_to_transaction(self, dto: TransactionDTO) -> Transaction:
        """Convert TransactionDTO to Transaction entity for processing"""
        from datetime import datetime

        # Parse date string to date object
        if isinstance(dto.date, str):
            date_obj = datetime.strptime(dto.date, "%Y-%m-%d").date()
        else:
            date_obj = dto.date

        transaction = Transaction(
            id=uuid4(),  # Temporary ID for processing
            date=date_obj,
            description=dto.description,
            normalized_description=dto.normalized_description,
            amount=Decimal(str(dto.amount)),
            account_id=dto.account_id,
            statement_id=dto.statement_id,
            source_type=SourceType.UPLOAD,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
        )
        return transaction

    def _create_unmatched_rule(self, normalized_description: str) -> None:
        """Create an enhancement rule for an unmatched normalized description with no category/counterparty"""
        try:
            rule = EnhancementRule(
                id=uuid4(),
                normalized_description_pattern=normalized_description,
                match_type="exact",  # Use string literal directly
                category_id=None,  # No category enhancement
                counterparty_account_id=None,  # No counterparty enhancement
                source="AI",  # Use string literal directly
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            self.enhancement_rule_repository.save(rule)
            logger.debug(f"Created unmatched rule for: {normalized_description}")

        except Exception as e:
            # Don't fail the enhancement if rule creation fails
            logger.warning(f"Failed to create unmatched rule for {normalized_description}: {e}")
