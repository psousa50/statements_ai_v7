from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4

from app.core.database import Base
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class CategorizationStatus(str, Enum):
    UNCATEGORIZED = "UNCATEGORIZED"
    CATEGORIZED = "CATEGORIZED"
    FAILURE = "FAILURE"


class SourceType(str, Enum):
    UPLOAD = "upload"
    MANUAL = "manual"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date, nullable=False, index=True)
    description = Column(String, nullable=False)
    normalized_description = Column(String, nullable=False, index=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    uploaded_file_id = Column(
        UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=True
    )
    uploaded_file = relationship("UploadedFile")

    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    category = relationship("Category")

    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    source = relationship("Source", back_populates="transactions")

    categorization_status = Column(
        SQLAlchemyEnum(CategorizationStatus),
        default=CategorizationStatus.UNCATEGORIZED,
        nullable=False,
    )

    categorization_confidence = Column(Numeric(precision=5, scale=4), nullable=True)

    # New ordering fields
    row_index = Column(Integer, nullable=True)
    sort_index = Column(Integer, nullable=False, default=0)
    source_type = Column(
        SQLAlchemyEnum(SourceType, values_callable=lambda x: [e.value for e in x]),
        default=SourceType.UPLOAD,
        nullable=False,
    )
    manual_position_after = Column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._running_balance: Optional[Decimal] = None

    @property
    def running_balance(self) -> Optional[Decimal]:
        """Get the running balance for this transaction"""
        return self._running_balance

    @running_balance.setter
    def running_balance(self, value: Optional[Decimal]):
        """Set the running balance for this transaction"""
        self._running_balance = value

    def mark_categorized(self):
        """Mark the transaction as categorized"""
        self.categorization_status = CategorizationStatus.CATEGORIZED

    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount}, category_id={self.category_id}, sort_index={self.sort_index})>"
