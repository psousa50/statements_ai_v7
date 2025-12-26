from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
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

    def __str__(self):
        return self.value


class EnhancementRuleSource(str, Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"


class EnhancementRule(Base):
    __tablename__ = "enhancement_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    normalized_description_pattern = Column(String, nullable=False, index=True)
    match_type = Column(
        SQLAlchemyEnum(MatchType, name="matchtype", values_callable=lambda x: [e.value for e in x]), nullable=False
    )

    # Optional amount constraints
    min_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    max_amount = Column(Numeric(precision=10, scale=2), nullable=True)

    # Optional date constraints
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Enhancement fields
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )
    counterparty_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=True,
    )

    # AI suggestion fields
    ai_suggested_category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )
    ai_category_confidence = Column(Numeric(precision=5, scale=4), nullable=True)
    ai_suggested_counterparty_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=True,
    )
    ai_counterparty_confidence = Column(Numeric(precision=5, scale=4), nullable=True)
    ai_processed_at = Column(DateTime, nullable=True)

    # Metadata
    source = Column(
        SQLAlchemyEnum(
            EnhancementRuleSource,
            name="enhancementrulesource",
        ),
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    category = relationship("Category", foreign_keys=[category_id])
    counterparty_account = relationship("Account", foreign_keys=[counterparty_account_id])
    ai_suggested_category = relationship("Category", foreign_keys=[ai_suggested_category_id])
    ai_suggested_counterparty = relationship("Account", foreign_keys=[ai_suggested_counterparty_id])

    @property
    def rule_type(self) -> str:
        has_category = self.category_id is not None
        has_counterparty = self.counterparty_account_id is not None

        if has_category and has_counterparty:
            return "Category + Counterparty"
        elif has_category:
            return "Category Only"
        elif has_counterparty:
            return "Counterparty Only"
        else:
            return "Unconfigured"

    @property
    def has_ai_category_suggestion(self) -> bool:
        return self.ai_suggested_category_id is not None

    @property
    def has_ai_counterparty_suggestion(self) -> bool:
        return self.ai_suggested_counterparty_id is not None

    @property
    def has_any_ai_suggestion(self) -> bool:
        return self.has_ai_category_suggestion or self.has_ai_counterparty_suggestion

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
