from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.domain.models.transaction import CategorizationStatus


@dataclass
class CategorizationResult:
    """Result of categorizing a single transaction"""

    transaction_id: UUID
    category_id: Optional[UUID]
    status: CategorizationStatus
    error_message: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class BatchCategorizationResult:
    """Result of categorizing a batch of transactions"""

    results: List[CategorizationResult]
    total_processed: int
    successful_count: int
    failed_count: int

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of the batch categorization"""
        if self.total_processed == 0:
            return 0.0
        return self.successful_count / self.total_processed

    def __post_init__(self):
        """Validate that counts match the results"""
        if len(self.results) != self.total_processed:
            raise ValueError("Results count must match total_processed")

        actual_successful = sum(1 for r in self.results if r.status == CategorizationStatus.CATEGORIZED)
        actual_failed = sum(1 for r in self.results if r.status == CategorizationStatus.FAILURE)

        if actual_successful != self.successful_count:
            raise ValueError("successful_count must match actual successful results")
        if actual_failed != self.failed_count:
            raise ValueError("failed_count must match actual failed results")
