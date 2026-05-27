from uuid import uuid4

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EnhancementRuleSplitLine(Base):
    __tablename__ = "enhancement_rule_split_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enhancement_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order = Column(Integer, nullable=False, default=0)
    label = Column(String, nullable=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=True)
    is_remainder = Column(Boolean, nullable=False, default=False)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )

    rule = relationship("EnhancementRule", back_populates="split_lines")
    category = relationship("Category", foreign_keys=[category_id])

    def __repr__(self):
        kind = "remainder" if self.is_remainder else f"fixed={self.amount}"
        return f"<EnhancementRuleSplitLine(id={self.id}, rule_id={self.rule_id}, {kind}, category_id={self.category_id})>"
