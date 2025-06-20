from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.domain.models.background_job import JobStatus
from app.domain.models.processing import BackgroundJobInfo
from app.domain.models.transaction import CategorizationStatus, CounterpartyStatus
from app.domain.models.transaction_categorization import CategorizationSource
from app.domain.models.transaction_counterparty_rule import CounterpartyRuleSource


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    parent_id: Optional[UUID] = None


class CategoryUpdate(CategoryBase):
    parent_id: Optional[UUID] = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    categories: Sequence[CategoryResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class AccountBase(BaseModel):
    name: str


class AccountCreate(AccountBase):
    pass


class AccountUpdate(AccountBase):
    pass


class AccountResponse(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class AccountListResponse(BaseModel):
    accounts: Sequence[AccountResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class AccountUploadResponse(BaseModel):
    accounts: Sequence[AccountResponse]
    total: int
    created: int
    updated: int

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    date: date
    description: str
    amount: Decimal = Field(..., ge=-1000000, le=1000000)


class TransactionCreate(TransactionBase):
    category_id: Optional[UUID] = None
    account_id: UUID
    counterparty_account_id: Optional[UUID] = None
    counterparty_status: Optional[CounterpartyStatus] = None


class TransactionUpdate(TransactionBase):
    category_id: Optional[UUID] = None
    account_id: UUID
    counterparty_account_id: Optional[UUID] = None
    counterparty_status: Optional[CounterpartyStatus] = None


class TransactionResponse(BaseModel):
    id: UUID
    date: date
    description: str
    normalized_description: str
    amount: Decimal
    created_at: "date"
    category_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    counterparty_account_id: Optional[UUID] = None
    counterparty_status: CounterpartyStatus
    categorization_status: CategorizationStatus
    running_balance: Optional[Decimal] = None
    row_index: Optional[int] = None
    sort_index: int
    source_type: str
    manual_position_after: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, value):
        if isinstance(value, datetime):
            return value.date()
        return value


class TransactionCreateRequest(BaseModel):
    date: date
    description: str
    amount: Decimal
    account_id: UUID
    category_id: Optional[UUID] = None
    counterparty_account_id: Optional[UUID] = None
    counterparty_status: Optional[CounterpartyStatus] = None
    after_transaction_id: Optional[UUID] = None


class TransactionUpdateRequest(BaseModel):
    date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    category_id: Optional[UUID] = None
    counterparty_account_id: Optional[UUID] = None
    counterparty_status: Optional[CounterpartyStatus] = None


class TransactionFilters(BaseModel):
    category_ids: Optional[List[UUID]] = None
    status: Optional[CategorizationStatus] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    description_search: Optional[str] = None
    account_id: Optional[UUID] = None
    counterparty_account_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class CategoryTotalResponse(BaseModel):
    category_id: Optional[UUID] = None
    total_amount: Decimal
    transaction_count: int

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("total_amount")
    def serialize_total_amount(self, value: Decimal) -> float:
        return float(value)


class CategoryTotalsResponse(BaseModel):
    totals: Sequence[CategoryTotalResponse]

    model_config = ConfigDict(from_attributes=True)


class CategoryTotalsListResponse(BaseModel):
    totals: List[CategoryTotalsResponse]
    total_transactions: int
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class ColumnMapping(BaseModel):
    date: str
    amount: str
    description: str
    category: Optional[str] = None


class StatementAnalysisResponse(BaseModel):
    uploaded_file_id: str
    file_type: str
    column_mapping: Dict[str, str]
    header_row_index: int
    data_start_row_index: int
    sample_data: list[list]
    account_id: Optional[str] = None
    # New transaction statistics fields - now mandatory
    total_transactions: int
    unique_transactions: int
    duplicate_transactions: int
    date_range: Tuple[str, str]
    total_amount: float
    total_debit: float
    total_credit: float

    model_config = ConfigDict(from_attributes=True)


class StatementUploadRequest(BaseModel):
    uploaded_file_id: str
    account_id: str
    column_mapping: Dict[str, str]
    header_row_index: int
    data_start_row_index: int


class BackgroundJobInfoResponse(BaseModel):
    job_id: str
    status: str
    remaining_transactions: int
    estimated_completion_seconds: int
    status_url: str

    model_config = ConfigDict(from_attributes=True)


class StatementUploadResponse(BaseModel):
    uploaded_file_id: str
    transactions_saved: int
    duplicated_transactions: int
    success: bool
    message: str

    # Synchronous categorization results
    total_processed: int
    rule_based_matches: int
    match_rate_percentage: float
    processing_time_ms: int

    # Background job information (if unmatched transactions exist)
    background_job: Optional[BackgroundJobInfoResponse] = None

    model_config = ConfigDict(from_attributes=True)


class StatementUploadResult(BaseModel):
    uploaded_file_id: str
    transactions_saved: int
    duplicated_transactions: int
    background_job_info: Optional["BackgroundJobInfo"] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionCategorizationCreateRequest(BaseModel):
    normalized_description: str
    category_id: UUID


class TransactionCategorizationUpdateRequest(BaseModel):
    category_id: UUID


class TransactionCategorizationResponse(BaseModel):
    id: UUID
    normalized_description: str
    category_id: UUID
    source: CategorizationSource
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None
    transaction_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionCategorizationListResponse(BaseModel):
    categorizations: List[TransactionCategorizationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class TransactionCategorizationFilters(BaseModel):
    description_search: Optional[str] = None
    category_ids: Optional[List[UUID]] = None
    source: Optional[CategorizationSource] = None


class BatchCategorizationRequest(BaseModel):
    transaction_ids: List[UUID]
    category_id: UUID


class CategorizationResultResponse(BaseModel):
    transaction_id: UUID
    category_id: Optional[UUID] = None
    status: CategorizationStatus
    error_message: Optional[str] = None
    confidence: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class BatchCategorizationResponse(BaseModel):
    results: List[CategorizationResultResponse]
    total_processed: int
    successful_count: int
    failed_count: int
    success: bool
    message: str

    model_config = ConfigDict(from_attributes=True)


class CategoryCreateRequest(BaseModel):
    name: str
    parent_id: Optional[UUID] = None


class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[UUID] = None


class SourceCreateRequest(BaseModel):
    name: str


class SourceUpdateRequest(BaseModel):
    name: str


# Background Job API Schemas
class JobStatusResponse(BaseModel):
    """Response for job status endpoint"""

    job_id: UUID
    status: JobStatus
    progress: Optional["JobProgressResponse"] = None
    result: Optional["JobResultResponse"] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobProgressResponse(BaseModel):
    """Job progress information"""

    total_transactions: int
    processed_transactions: int
    remaining_transactions: int
    completion_percentage: float
    estimated_completion_seconds: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class JobResultResponse(BaseModel):
    """Job completion results"""

    total_processed: int
    successfully_categorized: int
    failed_categorizations: int
    processing_time_ms: int

    model_config = ConfigDict(from_attributes=True)


# Transaction Categorization API Schemas
class TransactionCategorizationBase(BaseModel):
    normalized_description: str = Field(..., min_length=2, max_length=255)
    category_id: UUID
    source: CategorizationSource


class TransactionCategorizationCreate(TransactionCategorizationBase):
    pass


class TransactionCategorizationUpdate(TransactionCategorizationBase):
    pass


class TransactionCategorizationStatsResponse(BaseModel):
    summary: Dict[str, int]
    category_usage: List[Dict]
    top_rules_by_usage: List[Dict]
    unused_rules: List[Dict]

    model_config = ConfigDict(from_attributes=True)


class BulkUpdateTransactionsRequest(BaseModel):
    normalized_description: str
    category_id: Optional[str] = None


class BulkUpdateTransactionsResponse(BaseModel):
    updated_count: int
    message: str


class CategorizationResponse(BaseModel):
    categorized_count: int
    success: bool
    message: str

    model_config = ConfigDict(from_attributes=True)


# Transaction Counterparty Rule Schemas
class TransactionCounterpartyRuleBase(BaseModel):
    normalized_description: str
    counterparty_account_id: UUID
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    source: CounterpartyRuleSource = CounterpartyRuleSource.MANUAL


class TransactionCounterpartyRuleCreate(TransactionCounterpartyRuleBase):
    pass


class TransactionCounterpartyRuleUpdate(TransactionCounterpartyRuleBase):
    pass


class TransactionCounterpartyRuleResponse(BaseModel):
    id: UUID
    normalized_description: str
    counterparty_account_id: UUID
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    source: CounterpartyRuleSource
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionCounterpartyRuleListResponse(BaseModel):
    rules: Sequence[TransactionCounterpartyRuleResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
