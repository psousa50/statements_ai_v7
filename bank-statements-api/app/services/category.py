from typing import List, Optional
from uuid import UUID

from app.domain.models.category import Category
from app.ports.repositories.category import CategoryRepository


class CategoryService:
    """
    Application service for category operations.
    Contains business logic and uses the repository port.
    """

    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    def create_category(self, name: str, parent_id: Optional[UUID] = None) -> Category:
        """Create a new category"""
        # Validate parent exists if provided
        if parent_id and not self.category_repository.get_by_id(parent_id):
            raise ValueError(f"Parent category with ID {parent_id} not found")

        category = Category(name=name, parent_id=parent_id)
        return self.category_repository.create(category)

    def get_category(self, category_id: UUID) -> Optional[Category]:
        """Get a category by ID"""
        return self.category_repository.get_by_id(category_id)

    def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        return self.category_repository.get_all()

    def get_root_categories(self) -> List[Category]:
        """Get all root categories (categories without a parent)"""
        return self.category_repository.get_root_categories()

    def get_subcategories(self, parent_id: UUID) -> List[Category]:
        """Get all subcategories for a given parent category"""
        # Validate parent exists
        parent = self.category_repository.get_by_id(parent_id)
        if not parent:
            raise ValueError(f"Parent category with ID {parent_id} not found")

        return self.category_repository.get_subcategories(parent_id)

    def update_category(
        self, category_id: UUID, name: str, parent_id: Optional[UUID] = None
    ) -> Optional[Category]:
        """Update a category"""
        category = self.category_repository.get_by_id(category_id)
        if not category:
            return None

        # Validate parent exists if provided
        if parent_id and not self.category_repository.get_by_id(parent_id):
            raise ValueError(f"Parent category with ID {parent_id} not found")

        # Prevent circular references
        if parent_id == category_id:
            raise ValueError("A category cannot be its own parent")

        category.name = name
        category.parent_id = parent_id

        return self.category_repository.update(category)

    def delete_category(self, category_id: UUID) -> bool:
        """Delete a category"""
        # Check if category has subcategories
        subcategories = self.category_repository.get_subcategories(category_id)
        if subcategories:
            raise ValueError("Cannot delete a category that has subcategories")

        return self.category_repository.delete(category_id)
