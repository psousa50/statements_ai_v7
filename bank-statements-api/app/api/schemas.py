from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional, Sequence
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class SourceBase(BaseModel):
    name: str


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SourceBase):
    pass


class SourceResponse(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class SourceListResponse(BaseModel):
    sources: Sequence[SourceResponse]
    total: int


class TransactionBase(BaseModel):
    date: date
    description: str
    amount: Decimal = Field(..., ge=-1000000, le=1000000)


class TransactionCreate(TransactionBase):
    category_id: Optional[UUID] = None
    source_id: Optional[UUID] = None


class TransactionUpdate(TransactionBase):
    category_id: Optional[UUID] = None
    source_id: Optional[UUID] = None


class TransactionResponse(BaseModel):
    id: UUID
    date: date
    description: str
    amount: Decimal
    created_at: "date"
    category_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    categorization_status: CategorizationStatus

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, value):
        if isinstance(value, datetime):
            return value.date()
        return value


class TransactionListResponse(BaseModel):
    transactions: Sequence[TransactionResponse]
    total: int


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

    model_config = ConfigDict(from_attributes=True)


class StatementUploadRequest(BaseModel):
    source_id: str
    uploaded_file_id: str
    column_mapping: dict
    header_row_index: int
    data_start_row_index: int


class StatementUploadResponse(BaseModel):
    uploaded_file_id: str
    transactions_saved: int
    success: bool
    message: str

    model_config = ConfigDict(from_attributes=True)


class CategorizationResponse(BaseModel):
    categorized_count: int
    success: bool
    message: str

    model_config = ConfigDict(from_attributes=True)
