from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.domain.dto.statement_processing import FilterOperator, LogicalOperator
from app.domain.models.background_job import JobStatus
from app.domain.models.enhancement_rule import EnhancementRuleSource, MatchType
from app.domain.models.processing import BackgroundJobInfo
from app.domain.models.transaction import CategorizationStatus


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


class TransactionUpdate(TransactionBase):
    category_id: Optional[UUID] = None
    account_id: UUID
    counterparty_account_id: Optional[UUID] = None


class TransactionResponse(BaseModel):
    id: UUID
    date: date
    description: str
    normalized_description: str
    amount: Decimal
    created_at: date
    category_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    counterparty_account_id: Optional[UUID] = None
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
    after_transaction_id: Optional[UUID] = None


class EnhancementPreviewRequest(BaseModel):
    description: str
    amount: Optional[Decimal] = None
    transaction_date: Optional[date] = None


class EnhancementPreviewResponse(BaseModel):
    matched: bool
    rule_pattern: Optional[str] = None
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    counterparty_account_id: Optional[UUID] = None
    counterparty_account_name: Optional[str] = None


class TransactionUpdateRequest(BaseModel):
    date: date
    description: str
    amount: Decimal
    account_id: UUID
    category_id: Optional[UUID] = None
    counterparty_account_id: Optional[UUID] = None


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
    enhancement_rule: Optional["EnhancementRuleResponse"] = None

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


class CategoryTimeSeriesDataPoint(BaseModel):
    period: str
    category_id: Optional[UUID] = None
    total_amount: Decimal
    transaction_count: int

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("total_amount")
    def serialize_total_amount(self, value: Decimal) -> float:
        return float(value)


class CategoryTimeSeriesResponse(BaseModel):
    data_points: Sequence[CategoryTimeSeriesDataPoint]

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


class FilterConditionRequest(BaseModel):
    column_name: str
    operator: FilterOperator
    value: Optional[str] = None
    case_sensitive: bool = False


class RowFilterRequest(BaseModel):
    conditions: List[FilterConditionRequest]
    logical_operator: LogicalOperator = LogicalOperator.AND


class FilterPreviewResponse(BaseModel):
    total_rows: int
    included_rows: int
    excluded_rows: int
    included_row_indices: List[int]
    excluded_row_indices: List[int]


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
    # Optional filter suggestions for common patterns
    suggested_filters: Optional[List[FilterConditionRequest]] = None
    # Previously saved row filters for this file (if any)
    saved_row_filters: Optional[List[FilterConditionRequest]] = None

    model_config = ConfigDict(from_attributes=True)


class StatementUploadRequest(BaseModel):
    uploaded_file_id: str
    account_id: str
    column_mapping: Dict[str, str]
    header_row_index: int
    data_start_row_index: int
    row_filters: Optional[RowFilterRequest] = None


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


class CategoryCreateRequest(BaseModel):
    name: str
    parent_id: Optional[UUID] = None


class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[UUID] = None


class CategoryUploadResponse(BaseModel):
    """Response for category CSV upload"""

    categories_created: int
    categories_found: int
    total_processed: int
    categories: List[CategoryResponse]

    model_config = ConfigDict(from_attributes=True)


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


class BulkUpdateTransactionsRequest(BaseModel):
    normalized_description: str
    category_id: Optional[str] = None


class BulkUpdateTransactionsResponse(BaseModel):
    updated_count: int
    message: str


# Enhancement Rule Schemas
class EnhancementRuleBase(BaseModel):
    normalized_description_pattern: str = Field(..., min_length=1, max_length=255)
    match_type: MatchType
    category_id: Optional[UUID] = None
    counterparty_account_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source: EnhancementRuleSource = EnhancementRuleSource.MANUAL

    @field_validator("normalized_description_pattern")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

    @field_validator("min_amount", "max_amount")
    @classmethod
    def validate_amounts(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        return v


class EnhancementRuleCreate(EnhancementRuleBase):
    @field_validator("category_id", "counterparty_account_id")
    @classmethod
    def validate_at_least_one_enhancement(cls, v, info):
        # This will be validated in the service layer instead
        return v


class EnhancementRuleUpdate(EnhancementRuleBase):
    apply_to_existing: Optional[bool] = False


class EnhancementRulePreview(EnhancementRuleBase):
    """Schema for previewing enhancement rule effects without persisting the rule"""

    pass


class EnhancementRuleResponse(BaseModel):
    id: UUID
    normalized_description_pattern: str
    match_type: MatchType
    category_id: Optional[UUID] = None
    counterparty_account_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source: EnhancementRuleSource
    created_at: datetime
    updated_at: datetime
    rule_type: str
    # Optional populated fields
    category: Optional[CategoryResponse] = None
    counterparty_account: Optional[AccountResponse] = None
    transaction_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EnhancementRuleListResponse(BaseModel):
    rules: Sequence[EnhancementRuleResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class EnhancementRuleStatsResponse(BaseModel):
    summary: Dict[str, int]
    rule_type_usage: Optional[List[Dict]] = None
    category_usage: Optional[List[Dict]] = None
    counterparty_usage: Optional[List[Dict]] = None
    top_rules_by_usage: List[Dict]
    unused_rules: List[Dict]

    model_config = ConfigDict(from_attributes=True)


class MatchingTransactionsCountResponse(BaseModel):
    count: int
    date_range: Optional[Tuple[str, str]] = None
    amount_range: Optional[Tuple[float, float]] = None

    model_config = ConfigDict(from_attributes=True)


class CleanupUnusedRulesResponse(BaseModel):
    deleted_count: int
    message: str

    model_config = ConfigDict(from_attributes=True)


class StatementResponse(BaseModel):
    id: UUID
    account_id: UUID
    account_name: str
    filename: str
    file_type: str
    transaction_count: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecurringPatternResponse(BaseModel):
    description: str
    normalized_description: str
    interval_days: float
    average_amount: Decimal
    amount_variance: float
    transaction_count: int
    transaction_ids: List[str]
    category_id: Optional[str] = None
    first_transaction_date: date
    last_transaction_date: date
    total_annual_cost: Decimal

    @field_serializer("average_amount", "total_annual_cost")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class RecurringPatternsResponse(BaseModel):
    patterns: List[RecurringPatternResponse]
    summary: Dict[str, float]


class DescriptionGroupMemberResponse(BaseModel):
    id: UUID
    normalized_description: str

    model_config = ConfigDict(from_attributes=True)


class DescriptionGroupBase(BaseModel):
    name: str


class DescriptionGroupCreate(DescriptionGroupBase):
    normalized_descriptions: List[str]


class DescriptionGroupUpdate(DescriptionGroupBase):
    normalized_descriptions: List[str]


class DescriptionGroupResponse(BaseModel):
    id: UUID
    name: str
    members: List[DescriptionGroupMemberResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DescriptionGroupListResponse(BaseModel):
    groups: Sequence[DescriptionGroupResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
