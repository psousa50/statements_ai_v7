from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategorizationStatus(str, Enum):
    UNCATEGORIZED = "UNCATEGORIZED"
    CATEGORIZED = "CATEGORIZED"
    FAILURE = "FAILURE"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date, nullable=False, index=True)
    description = Column(String, nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    uploaded_file_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=True)
    uploaded_file = relationship("UploadedFile")

    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    category = relationship("Category")

    categorization_status = Column(
        SQLAlchemyEnum(CategorizationStatus),
        default=CategorizationStatus.UNCATEGORIZED,
        nullable=False,
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount}, category_id={self.category_id})>"
