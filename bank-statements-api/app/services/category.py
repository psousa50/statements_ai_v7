import csv
from io import StringIO
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
        if parent_id:
            parent = self.category_repository.get_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent category with ID {parent_id} not found")

            if parent.parent_id:
                raise ValueError("Cannot create more than 2 levels of categories. Parent category already has a parent.")

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
        self,
        category_id: UUID,
        name: str,
        parent_id: Optional[UUID] = None,
    ) -> Optional[Category]:
        """Update a category"""
        category = self.category_repository.get_by_id(category_id)
        if not category:
            return None

        if parent_id == category_id:
            raise ValueError("A category cannot be its own parent")

        if parent_id:
            parent = self.category_repository.get_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent category with ID {parent_id} not found")

            if parent.parent_id:
                raise ValueError("Cannot create more than 2 levels of categories. Parent category already has a parent.")

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

    def upsert_category(self, name: str, parent_id: Optional[UUID] = None) -> Category:
        """Create or update a category (upsert operation)"""
        if parent_id:
            parent = self.category_repository.get_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent category with ID {parent_id} not found")

            if parent.parent_id:
                raise ValueError("Cannot create more than 2 levels of categories. Parent category already has a parent.")

        existing_category = self.category_repository.get_by_name(name, parent_id)
        if existing_category:
            return existing_category

        category = Category(name=name, parent_id=parent_id)
        return self.category_repository.create(category)

    def upsert_categories_from_csv(self, csv_content: str) -> List[Category]:
        """Create categories from CSV content with upsert logic"""
        categories = []
        parent_cache = {}

        try:
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)

            # Validate required columns
            if "parent_name" not in reader.fieldnames or "name" not in reader.fieldnames:
                raise ValueError("CSV must contain 'parent_name' and 'name' columns")

            for row in reader:
                parent_name = row.get("parent_name", "").strip()
                name = row.get("name", "").strip()

                if not name:
                    continue  # Skip rows without a name

                parent_id = None
                if parent_name:
                    # Check cache first
                    if parent_name in parent_cache:
                        parent_id = parent_cache[parent_name]
                    else:
                        # Create or get parent category
                        parent_category = self.upsert_category(parent_name, None)
                        parent_id = parent_category.id
                        parent_cache[parent_name] = parent_id

                # Create or get category
                category = self.upsert_category(name, parent_id)
                categories.append(category)

            return categories

        except Exception as e:
            raise ValueError(f"Error processing CSV: {str(e)}")
