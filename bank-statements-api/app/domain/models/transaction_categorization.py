from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategorizationSource(str, Enum):
    MANUAL = "MANUAL"
    AI = "AI"


class TransactionCategorization(Base):
    __tablename__ = "transaction_categorization"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    normalized_description = Column(String, nullable=False, unique=True, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    source = Column(SQLAlchemyEnum(CategorizationSource), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    category = relationship("Category")

    def __repr__(self):
        return (
            f"<TransactionCategorization(id={self.id}, "
            f"normalized_description={self.normalized_description}, "
            f"category_id={self.category_id}, source={self.source})>"
        )
