from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.models.enhancement_rule import MatchType


class EnhancementRulePattern(Base):
    __tablename__ = "enhancement_rule_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enhancement_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_description = Column(String, nullable=False, index=True)
    match_type = Column(
        SQLAlchemyEnum(MatchType, name="matchtype", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    sort_order = Column(Integer, nullable=False, default=0)

    rule = relationship("EnhancementRule", back_populates="patterns")

    __table_args__ = (
        UniqueConstraint(
            "rule_id",
            "normalized_description",
            name="uq_enhancement_rule_patterns_rule_description",
        ),
    )

    def __repr__(self):
        return (
            f"<EnhancementRulePattern(id={self.id}, rule_id={self.rule_id}, "
            f"normalized_description={self.normalized_description}, match_type={self.match_type})>"
        )
