from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MatchType(str, Enum):
    EXACT = "exact"
    PREFIX = "prefix"
    INFIX = "infix"


class EnhancementRuleSource(str, Enum):
    MANUAL = "MANUAL"
    AI = "AI"


class EnhancementRule(Base):
    __tablename__ = "enhancement_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    normalized_description_pattern = Column(String, nullable=False, index=True)
    match_type = Column(SQLAlchemyEnum(MatchType), nullable=False)

    # Optional amount constraints
    min_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    max_amount = Column(Numeric(precision=10, scale=2), nullable=True)

    # Optional date constraints
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Enhancement fields
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    counterparty_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)

    # Metadata
    source = Column(SQLAlchemyEnum(EnhancementRuleSource), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    category = relationship("Category")
    counterparty_account = relationship("Account")

    def matches_transaction(self, transaction) -> bool:
        """Check if this rule matches the given transaction"""
        # Check description pattern
        if self.match_type == MatchType.EXACT:
            if transaction.normalized_description != self.normalized_description_pattern:
                return False
        elif self.match_type == MatchType.PREFIX:
            if not transaction.normalized_description.startswith(self.normalized_description_pattern):
                return False
        elif self.match_type == MatchType.INFIX:
            if self.normalized_description_pattern not in transaction.normalized_description:
                return False

        # Check amount constraints
        if self.min_amount is not None and transaction.amount < self.min_amount:
            return False
        if self.max_amount is not None and transaction.amount > self.max_amount:
            return False

        # Check date constraints
        if self.start_date is not None and transaction.date < self.start_date:
            return False
        if self.end_date is not None and transaction.date > self.end_date:
            return False

        return True

    def __repr__(self):
        return (
            f"<EnhancementRule(id={self.id}, "
            f"pattern={self.normalized_description_pattern}, "
            f"match_type={self.match_type}, "
            f"category_id={self.category_id}, "
            f"counterparty_account_id={self.counterparty_account_id})>"
        )
