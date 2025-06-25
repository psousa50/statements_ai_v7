from typing import List, Optional
from uuid import UUID

from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.processing import BackgroundJobInfo
from app.domain.models.statement import Statement


class ParsedStatement:
    """Result of parsing a statement file"""

    def __init__(
        self,
        uploaded_file_id: UUID,
        transaction_dtos: List[TransactionDTO],
        account_id: UUID,
    ):
        self.uploaded_file_id = uploaded_file_id
        self.transaction_dtos = transaction_dtos
        self.account_id = account_id


class EnhancedTransactions:
    """Result of enhancing transactions with rule-based processing"""

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


class SavedStatement:
    """Result of saving a statement and transactions to database"""

    def __init__(
        self,
        statement: Statement,
        uploaded_file_id: str,
        transactions_saved: int,
        duplicated_transactions: int,
    ):
        self.statement = statement
        self.uploaded_file_id = uploaded_file_id
        self.transactions_saved = transactions_saved
        self.duplicated_transactions = duplicated_transactions


class ScheduledJobs:
    """Result of scheduling background jobs"""

    def __init__(
        self,
        categorization_job_info: Optional[BackgroundJobInfo] = None,
        counterparty_job_info: Optional[BackgroundJobInfo] = None,
    ):
        self.categorization_job_info = categorization_job_info
        self.counterparty_job_info = counterparty_job_info

    @property
    def has_categorization_job(self) -> bool:
        return self.categorization_job_info is not None

    @property
    def has_counterparty_job(self) -> bool:
        return self.counterparty_job_info is not None
