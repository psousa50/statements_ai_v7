import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from app.common.text_normalization import normalize_description
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
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

    def enhance_transactions(self, user_id: UUID, transaction_dtos: List[TransactionDTO]) -> EnhancementResult:
        start_time_ms = int(time.time() * 1000)

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

        transactions = []
        normalized_descriptions_set = set()

        for dto in transaction_dtos:
            dto.normalized_description = normalize_description(dto.description)
            normalized_descriptions_set.add(dto.normalized_description)
            transaction = self._dto_to_transaction(dto)
            transactions.append(transaction)

        matching_rules = self.enhancement_rule_repository.find_matching_rules_batch(list(normalized_descriptions_set), user_id)
        logger.debug(
            f"Retrieved {len(matching_rules)} matching rules for {len(normalized_descriptions_set)} unique descriptions"
        )

        rules_map = self._build_rules_map(transactions, matching_rules)
        enhanced_transactions = self._apply_rules_from_map(transactions, rules_map)

        matched_count = 0
        unmatched_transactions = []

        for i, transaction in enumerate(enhanced_transactions):
            dto = transaction_dtos[i]
            dto.category_id = transaction.category_id
            dto.categorization_status = transaction.categorization_status
            dto.counterparty_account_id = transaction.counterparty_account_id

            if transaction.category_id or transaction.counterparty_account_id:
                matched_count += 1
            else:
                unmatched_transactions.append(transaction)

        unique_normalized_descriptions = {t.normalized_description for t in unmatched_transactions if t.normalized_description}
        for normalized_description in unique_normalized_descriptions:
            self._create_unmatched_rule(user_id, normalized_description)

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

    def _create_unmatched_rule(self, user_id: UUID, normalized_description: str) -> None:
        try:
            existing_rule = self.enhancement_rule_repository.find_by_normalized_description(normalized_description, user_id)

            if existing_rule:
                logger.debug(f"Rule already exists for normalized description: {normalized_description}")
                return

            rule = EnhancementRule(
                id=uuid4(),
                user_id=user_id,
                normalized_description_pattern=normalized_description,
                match_type=MatchType.EXACT,
                category_id=None,
                counterparty_account_id=None,
                source=EnhancementRuleSource.AUTO,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            self.enhancement_rule_repository.save(rule)
            logger.debug(f"Created unmatched rule for: {normalized_description}")

        except Exception as e:
            logger.warning(f"Failed to create unmatched rule for {normalized_description}: {e}")

    def _build_rules_map(self, transactions: List[Transaction], rules: List[EnhancementRule]) -> dict:
        """
        Build a lookup map from normalized_description to the best matching rule.
        For each transaction, find the first matching rule (rules are already sorted by precedence).
        """
        rules_map = {}

        for transaction in transactions:
            if transaction.normalized_description in rules_map:
                continue

            for rule in rules:
                if rule.matches_transaction(transaction):
                    rules_map[transaction.normalized_description] = rule
                    break

        return rules_map

    def _apply_rules_from_map(self, transactions: List[Transaction], rules_map: dict) -> List[Transaction]:
        """Apply enhancement rules to transactions using the lookup map"""
        for transaction in transactions:
            rule = rules_map.get(transaction.normalized_description)
            if rule:
                if rule.category_id is not None:
                    transaction.category_id = rule.category_id
                    transaction.mark_rule_based_categorization()

                if rule.counterparty_account_id is not None:
                    transaction.counterparty_account_id = rule.counterparty_account_id
                    transaction.mark_rule_based_counterparty()

        return transactions
