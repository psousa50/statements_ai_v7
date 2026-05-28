from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Numeric
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
    patterns = relationship(
        "EnhancementRulePattern",
        back_populates="rule",
        cascade="all, delete-orphan",
        order_by="EnhancementRulePattern.sort_order",
        lazy="selectin",
    )
    category = relationship("Category", foreign_keys=[category_id])
    counterparty_account = relationship("Account", foreign_keys=[counterparty_account_id])
    ai_suggested_category = relationship("Category", foreign_keys=[ai_suggested_category_id])
    ai_suggested_counterparty = relationship("Account", foreign_keys=[ai_suggested_counterparty_id])
    split_lines = relationship(
        "EnhancementRuleSplitLine",
        back_populates="rule",
        cascade="all, delete-orphan",
        order_by="EnhancementRuleSplitLine.sort_order",
        lazy="selectin",
    )

    @property
    def has_split_template(self) -> bool:
        return bool(self.split_lines)

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

    def _pattern_matches(self, pattern, normalized_description: str) -> bool:
        if pattern.match_type == MatchType.EXACT:
            return normalized_description == pattern.normalized_description
        if pattern.match_type == MatchType.PREFIX:
            return normalized_description.startswith(pattern.normalized_description)
        if pattern.match_type == MatchType.INFIX:
            return pattern.normalized_description in normalized_description
        return False

    def matches_transaction(self, transaction) -> bool:
        if not any(self._pattern_matches(p, transaction.normalized_description) for p in self.patterns):
            return False

        if self.min_amount is not None and transaction.amount < self.min_amount:
            return False
        if self.max_amount is not None and transaction.amount > self.max_amount:
            return False

        if self.start_date is not None and transaction.date < self.start_date:
            return False
        if self.end_date is not None and transaction.date > self.end_date:
            return False

        return True

    def __repr__(self):
        pattern_repr = ",".join(p.normalized_description for p in (self.patterns or []))
        return (
            f"<EnhancementRule(id={self.id}, "
            f"patterns=[{pattern_repr}], "
            f"category_id={self.category_id}, "
            f"counterparty_account_id={self.counterparty_account_id})>"
        )
