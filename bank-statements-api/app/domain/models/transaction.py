from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategorizationStatus(str, Enum):
    UNCATEGORIZED = "UNCATEGORIZED"
    RULE_BASED = "RULE_BASED"
    MANUAL = "MANUAL"
    FAILURE = "FAILURE"


class SourceType(str, Enum):
    UPLOAD = "upload"
    MANUAL = "manual"


class CounterpartyStatus(str, Enum):
    UNPROCESSED = "UNPROCESSED"
    RULE_BASED = "RULE_BASED"
    MANUAL = "MANUAL"
    FAILURE = "FAILURE"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date, nullable=False, index=True)
    description = Column(String, nullable=False)
    normalized_description = Column(String, nullable=False, index=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    statement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("statements.id"),
        nullable=False,
    )
    statement = relationship("Statement", back_populates="transactions")

    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )
    category = relationship("Category")

    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=False,
    )
    account = relationship(
        "Account",
        foreign_keys=[account_id],
        back_populates="transactions",
    )

    counterparty_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=True,
    )
    counterparty_account = relationship(
        "Account",
        foreign_keys=[counterparty_account_id],
        back_populates="counterparty_transactions",
    )

    categorization_status = Column(
        SQLAlchemyEnum(CategorizationStatus),
        default=CategorizationStatus.UNCATEGORIZED,
        nullable=False,
    )

    categorization_confidence = Column(Numeric(precision=5, scale=4), nullable=True)

    counterparty_status = Column(
        SQLAlchemyEnum(CounterpartyStatus),
        default=CounterpartyStatus.UNPROCESSED,
        nullable=False,
    )

    # New ordering fields
    row_index = Column(Integer, nullable=False)
    sort_index = Column(Integer, nullable=False, default=0)
    source_type = Column(
        SQLAlchemyEnum(
            SourceType,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=SourceType.UPLOAD,
        nullable=False,
    )
    manual_position_after = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id"),
        nullable=True,
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
        """Mark the transaction as categorized (for backward compatibility)"""
        self.categorization_status = CategorizationStatus.RULE_BASED

    def mark_rule_based_categorization(self):
        """Mark the transaction as categorized by a rule"""
        self.categorization_status = CategorizationStatus.RULE_BASED

    def mark_manual_categorization(self):
        """Mark the transaction as manually categorized"""
        self.categorization_status = CategorizationStatus.MANUAL

    def mark_rule_based_counterparty(self):
        """Mark the counterparty as assigned by a rule"""
        self.counterparty_status = CounterpartyStatus.RULE_BASED

    def mark_manual_counterparty(self):
        """Mark the counterparty as manually assigned"""
        self.counterparty_status = CounterpartyStatus.MANUAL

    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount}, category_id={self.category_id}, sort_index={self.sort_index})>"
