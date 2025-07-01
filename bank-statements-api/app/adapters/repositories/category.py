from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.category import Category
from app.ports.repositories.category import CategoryRepository


class SQLAlchemyCategoryRepository(CategoryRepository):
    """
    SQLAlchemy implementation of the CategoryRepository.
    Adapter in the Hexagonal Architecture pattern.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, category: Category) -> Category:
        self.db_session.add(category)
        self.db_session.commit()
        self.db_session.refresh(category)
        return category

    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        return self.db_session.query(Category).filter(Category.id == category_id).first()

    def get_all(self) -> List[Category]:
        return self.db_session.query(Category).all()

    def get_root_categories(self) -> List[Category]:
        return self.db_session.query(Category).filter(Category.parent_id.is_(None)).all()

    def get_subcategories(self, parent_id: UUID) -> List[Category]:
        return self.db_session.query(Category).filter(Category.parent_id == parent_id).all()

    def update(self, category: Category) -> Category:
        self.db_session.commit()
        self.db_session.refresh(category)
        return category

    def delete(self, category_id: UUID) -> bool:
        category = self.get_by_id(category_id)
        if category:
            self.db_session.delete(category)
            self.db_session.commit()
            return True
        return False

    def get_by_name(self, name: str, parent_id: Optional[UUID] = None) -> Optional[Category]:
        query = self.db_session.query(Category).filter(Category.name == name)
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        else:
            query = query.filter(Category.parent_id.is_(None))
        return query.first()
