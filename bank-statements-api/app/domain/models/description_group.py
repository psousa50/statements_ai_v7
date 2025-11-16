from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DescriptionGroup(Base):
    __tablename__ = "description_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
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

    members = relationship(
        "DescriptionGroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<DescriptionGroup(id={self.id}, name={self.name})>"


class DescriptionGroupMember(Base):
    __tablename__ = "description_group_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("description_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_description = Column(String, nullable=False, index=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    group = relationship("DescriptionGroup", back_populates="members")

    def __repr__(self):
        return f"<DescriptionGroupMember(id={self.id}, group_id={self.group_id}, normalized_description={self.normalized_description})>"
