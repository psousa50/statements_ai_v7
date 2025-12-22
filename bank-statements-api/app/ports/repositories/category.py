from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.category import Category


class CategoryRepository(ABC):
    @abstractmethod
    def create(self, category: Category) -> Category:
        pass

    @abstractmethod
    def get_by_id(self, category_id: UUID, user_id: UUID) -> Optional[Category]:
        pass

    @abstractmethod
    def get_all(self, user_id: UUID) -> List[Category]:
        pass

    @abstractmethod
    def get_root_categories(self, user_id: UUID) -> List[Category]:
        pass

    @abstractmethod
    def get_subcategories(self, parent_id: UUID, user_id: UUID) -> List[Category]:
        pass

    @abstractmethod
    def update(self, category: Category) -> Category:
        pass

    @abstractmethod
    def delete(self, category_id: UUID, user_id: UUID) -> bool:
        pass

    @abstractmethod
    def get_by_name(self, name: str, user_id: UUID, parent_id: Optional[UUID] = None) -> Optional[Category]:
        pass
