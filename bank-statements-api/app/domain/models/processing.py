from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.domain.models.background_job import JobStatus


@dataclass
class ProcessingProgress:
    """Progress information for background processing"""

    current_batch: int
    total_batches: int
    processed_transactions: int
    total_transactions: int
    phase: str
    estimated_completion_seconds: Optional[int] = None

    @property
    def percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_transactions == 0:
            return 0.0
        return (self.processed_transactions / self.total_transactions) * 100

    @property
    def batch_percentage(self) -> float:
        """Calculate batch progress percentage"""
        if self.total_batches == 0:
            return 0.0
        return (self.current_batch / self.total_batches) * 100


@dataclass
class SyncCategorizationResult:
    """Result of synchronous rule-based categorization"""

    total_processed: int
    rule_based_matches: int
    unmatched_transaction_ids: List[UUID]
    processing_time_ms: int
    match_rate_percentage: float

    @property
    def has_unmatched_transactions(self) -> bool:
        """Check if there are unmatched transactions requiring AI processing"""
        return len(self.unmatched_transaction_ids) > 0


@dataclass
class AsyncCategorizationResult:
    """Result of asynchronous AI categorization"""

    total_processed: int
    ai_categorized: int
    failed: int
    new_rules_learned: int
    processing_time_ms: int
    conflicts_resolved: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate AI categorization success rate"""
        if self.total_processed == 0:
            return 0.0
        return (self.ai_categorized / self.total_processed) * 100


@dataclass
class BackgroundJobInfo:
    """Information about a background job for API responses"""

    job_id: UUID
    status: JobStatus
    remaining_transactions: int
    estimated_completion_seconds: Optional[int] = None
    status_url: Optional[str] = None


@dataclass
class JobStatusResponse:
    """Response model for job status API"""

    job_id: UUID
    status: JobStatus
    created_at: str
    progress: Optional[ProcessingProgress] = None
    results: Optional[AsyncCategorizationResult] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class DTOProcessingResult:
    """Result of processing transaction DTOs (before persistence)"""

    processed_dtos: List  # List of processed TransactionDTOs
    total_processed: int
    rule_based_matches: int
    unmatched_dto_count: int
    processing_time_ms: int
    match_rate_percentage: float

    @property
    def has_unmatched_transactions(self) -> bool:
        """Check if there are unmatched transactions requiring AI processing"""
        return self.unmatched_dto_count > 0
