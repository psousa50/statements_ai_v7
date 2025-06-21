from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CounterpartyRuleSource(str, Enum):
    MANUAL = "MANUAL"
    AI = "AI"


class TransactionCounterpartyRule(Base):
    __tablename__ = "transaction_counterparty_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    normalized_description = Column(String, nullable=False, unique=True, index=True)
    counterparty_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    min_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    max_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    source = Column(SQLAlchemyEnum(CounterpartyRuleSource), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    counterparty_account = relationship("Account")

    def __repr__(self):
        return (
            f"<TransactionCounterpartyRule(id={self.id}, "
            f"normalized_description={self.normalized_description}, "
            f"counterparty_account_id={self.counterparty_account_id}, "
            f"min_amount={self.min_amount}, max_amount={self.max_amount}, "
            f"source={self.source})>"
        )
