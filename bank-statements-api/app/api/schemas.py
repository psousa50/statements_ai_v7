from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Sequence
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

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


class TransactionBase(BaseModel):
    date: date
    description: str
    amount: Decimal = Field(..., ge=-1000000, le=1000000)


class TransactionCreate(TransactionBase):
    category_id: Optional[UUID] = None


class TransactionUpdate(TransactionBase):
    category_id: Optional[UUID] = None


class TransactionResponse(BaseModel):
    id: UUID
    date: date
    description: str
    amount: Decimal
    created_at: date
    category_id: Optional[UUID] = None
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
