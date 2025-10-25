from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Statement(Base):
    __tablename__ = "statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=False,
    )
    filename = Column(Text, nullable=False)
    file_type = Column(String, nullable=False)
    content = Column(LargeBinary, nullable=False)
    transaction_count = Column(Integer, nullable=True)
    date_from = Column(Date, nullable=True)
    date_to = Column(Date, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    account = relationship("Account", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement")

    def __repr__(self):
        return f"<Statement(id={self.id}, account_id={self.account_id}, filename={self.filename})>"
