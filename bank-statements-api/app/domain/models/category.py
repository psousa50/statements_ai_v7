from uuid import uuid4

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


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
    include_in_spending = Column(Boolean, nullable=False, default=True, server_default="true")

    user = relationship("User", back_populates="categories")
    parent = relationship(
        "Category",
        remote_side=[id],
        backref="subcategories",
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("include_in_spending", True)
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, parent_id={self.parent_id})>"
