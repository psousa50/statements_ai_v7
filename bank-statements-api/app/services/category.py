import csv
from io import StringIO
from typing import List, Optional
from uuid import UUID

from app.domain.models.category import Category
from app.ports.repositories.category import CategoryRepository


class CategoryService:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    def create_category(
        self, name: str, user_id: UUID, parent_id: Optional[UUID] = None, color: Optional[str] = None
    ) -> Category:
        if parent_id:
            parent = self.category_repository.get_by_id(parent_id, user_id)
            if not parent:
                raise ValueError(f"Parent category with ID {parent_id} not found")

            if parent.parent_id:
                raise ValueError("Cannot create more than 2 levels of categories. Parent category already has a parent.")

        category = Category(name=name, user_id=user_id, parent_id=parent_id, color=color)
        return self.category_repository.create(category)

    def get_category(self, category_id: UUID, user_id: UUID) -> Optional[Category]:
        return self.category_repository.get_by_id(category_id, user_id)

    def get_all_categories(self, user_id: UUID) -> List[Category]:
        return self.category_repository.get_all(user_id)

    def get_root_categories(self, user_id: UUID) -> List[Category]:
        return self.category_repository.get_root_categories(user_id)

    def get_subcategories(self, parent_id: UUID, user_id: UUID) -> List[Category]:
        parent = self.category_repository.get_by_id(parent_id, user_id)
        if not parent:
            raise ValueError(f"Parent category with ID {parent_id} not found")

        return self.category_repository.get_subcategories(parent_id, user_id)

    def update_category(
        self,
        category_id: UUID,
        name: str,
        user_id: UUID,
        parent_id: Optional[UUID] = None,
        color: Optional[str] = None,
    ) -> Optional[Category]:
        category = self.category_repository.get_by_id(category_id, user_id)
        if not category:
            return None

        if parent_id == category_id:
            raise ValueError("A category cannot be its own parent")

        if parent_id:
            parent = self.category_repository.get_by_id(parent_id, user_id)
            if not parent:
                raise ValueError(f"Parent category with ID {parent_id} not found")

            if parent.parent_id:
                raise ValueError("Cannot create more than 2 levels of categories. Parent category already has a parent.")

        category.name = name
        category.parent_id = parent_id
        category.color = color

        return self.category_repository.update(category)

    def delete_category(self, category_id: UUID, user_id: UUID) -> bool:
        subcategories = self.category_repository.get_subcategories(category_id, user_id)
        if subcategories:
            raise ValueError("Cannot delete a category that has subcategories")

        return self.category_repository.delete(category_id, user_id)

    def upsert_category(
        self, name: str, user_id: UUID, parent_id: Optional[UUID] = None, color: Optional[str] = None
    ) -> Category:
        if parent_id:
            parent = self.category_repository.get_by_id(parent_id, user_id)
            if not parent:
                raise ValueError(f"Parent category with ID {parent_id} not found")

            if parent.parent_id:
                raise ValueError("Cannot create more than 2 levels of categories. Parent category already has a parent.")

        existing_category = self.category_repository.get_by_name(name, user_id, parent_id)
        if existing_category:
            if color and existing_category.color != color:
                existing_category.color = color
                return self.category_repository.update(existing_category)
            return existing_category

        category = Category(name=name, user_id=user_id, parent_id=parent_id, color=color)
        return self.category_repository.create(category)

    def upsert_categories_from_csv(self, csv_content: str, user_id: UUID) -> List[Category]:
        categories = []
        parent_cache = {}
        parent_colors = {}

        try:
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)

            if "parent_name" not in reader.fieldnames or "name" not in reader.fieldnames:
                raise ValueError("CSV must contain 'parent_name' and 'name' columns")

            for row in reader:
                parent_name = row.get("parent_name", "").strip()
                name = row.get("name", "").strip()
                color = row.get("color", "").strip() or None

                if not name:
                    continue

                parent_id = None
                if parent_name:
                    if parent_name in parent_cache:
                        parent_id = parent_cache[parent_name]
                    else:
                        parent_color = parent_colors.get(parent_name)
                        parent_category = self.upsert_category(parent_name, user_id, None, parent_color)
                        parent_id = parent_category.id
                        parent_cache[parent_name] = parent_id
                else:
                    parent_colors[name] = color

                category = self.upsert_category(name, user_id, parent_id, color)
                categories.append(category)

            return categories

        except Exception as e:
            raise ValueError(f"Error processing CSV: {str(e)}")
