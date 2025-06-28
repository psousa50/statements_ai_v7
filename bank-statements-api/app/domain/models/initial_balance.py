from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class InitialBalance(Base):
    __tablename__ = "initial_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=False,
    )
    balance_date = Column(Date, nullable=False)
    balance_amount = Column(Numeric(precision=10, scale=2), nullable=False)
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

    account = relationship("Account")

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "balance_date",
            name="uq_initial_balance_account_date",
        ),
    )

    def __repr__(self):
        return f"<InitialBalance(id={self.id}, account_id={self.account_id}, balance_date={self.balance_date}, balance_amount={self.balance_amount})>"
