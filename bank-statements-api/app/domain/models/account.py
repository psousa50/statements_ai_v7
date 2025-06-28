from uuid import uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False, unique=True)

    transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.account_id",
        back_populates="account",
    )
    counterparty_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.counterparty_account_id",
        back_populates="counterparty_account",
    )
    statements = relationship("Statement", back_populates="account")

    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name})>"
