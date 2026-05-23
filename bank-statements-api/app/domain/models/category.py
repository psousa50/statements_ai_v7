from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategoryKind(str, PyEnum):
    NEED = "need"
    COMFORT = "comfort"
    UNPLANNED = "unplanned"
    EXTRA = "extra"


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    color = Column(String(7), nullable=True)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )
    exclude_from_spending = Column(Boolean, nullable=False, default=False, server_default="false")
    kind = Column(
        Enum(CategoryKind, name="category_kind", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CategoryKind.NEED,
        server_default=CategoryKind.NEED.value,
    )

    user = relationship("User", back_populates="categories")
    parent = relationship(
        "Category",
        remote_side=[id],
        backref="subcategories",
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("exclude_from_spending", False)
        kwargs.setdefault("kind", CategoryKind.NEED)
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, parent_id={self.parent_id})>"
