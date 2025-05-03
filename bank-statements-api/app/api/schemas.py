from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.transaction import CategorizationStatus


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    parent_id: Optional[UUID] = None


class CategoryUpdate(CategoryBase):
    parent_id: Optional[UUID] = None


class CategoryResponse(CategoryBase):
    id: UUID
    parent_id: Optional[UUID] = None

    class Config:
        orm_mode = True


class CategoryListResponse(BaseModel):
    categories: List[CategoryResponse]
    total: int


class TransactionBase(BaseModel):
    date: date
    description: str
    amount: Decimal = Field(..., ge=-1000000, le=1000000)


class TransactionCreate(TransactionBase):
    category_id: Optional[UUID] = None


class TransactionUpdate(TransactionBase):
    category_id: Optional[UUID] = None


class TransactionResponse(TransactionBase):
    id: UUID
    created_at: date
    category_id: Optional[UUID] = None
    categorization_status: CategorizationStatus

    class Config:
        orm_mode = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
