from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.category import Category


class CategoryRepository(ABC):
    """
    Port (interface) for category repository operations.
    Following Hexagonal Architecture pattern.
    """

    @abstractmethod
    def create(self, category: Category) -> Category:
        """Create a new category"""
        pass

    @abstractmethod
    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Get a category by ID"""
        pass

    @abstractmethod
    def get_all(self) -> List[Category]:
        """Get all categories"""
        pass

    @abstractmethod
    def get_root_categories(self) -> List[Category]:
        """Get all root categories (categories without a parent)"""
        pass

    @abstractmethod
    def get_subcategories(self, parent_id: UUID) -> List[Category]:
        """Get all subcategories for a given parent category"""
        pass

    @abstractmethod
    def update(self, category: Category) -> Category:
        """Update a category"""
        pass

    @abstractmethod
    def delete(self, category_id: UUID) -> bool:
        """Delete a category"""
        pass
