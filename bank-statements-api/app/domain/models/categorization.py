from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import UUID


class CategorizationResultStatus(str, Enum):
    CATEGORIZED = "CATEGORIZED"
    UNCATEGORIZED = "UNCATEGORIZED"
    FAILURE = "FAILURE"


@dataclass
class CategorizationResult:
    transaction_id: UUID
    category_id: Optional[UUID]
    status: CategorizationResultStatus
    confidence: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class RuleCategorizationResult:
    rule_id: UUID
    suggested_category_id: Optional[UUID]
    confidence: Optional[float] = None
    error_message: Optional[str] = None

    @property
    def is_successful(self) -> bool:
        return self.suggested_category_id is not None and self.confidence is not None


@dataclass
class RuleCounterpartyResult:
    rule_id: UUID
    suggested_counterparty_id: Optional[UUID]
    confidence: Optional[float] = None
    error_message: Optional[str] = None

    @property
    def is_successful(self) -> bool:
        return self.suggested_counterparty_id is not None and self.confidence is not None
