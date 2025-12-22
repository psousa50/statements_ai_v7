from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.models.category import Category
from app.ports.repositories.category import CategoryRepository
from app.services.category import CategoryService


class TestCategoryService:

    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_repository(self):
        repository = MagicMock(spec=CategoryRepository)
        return repository

    @pytest.fixture
    def service(self, mock_repository):
        return CategoryService(mock_repository)

    @pytest.fixture
    def parent_category(self, user_id):
        return Category(
            id=uuid4(),
            name="Parent Category",
            parent_id=None,
            user_id=user_id,
        )

    @pytest.fixture
    def child_category(self, parent_category, user_id):
        return Category(
            id=uuid4(),
            name="Child Category",
            parent_id=parent_category.id,
            user_id=user_id,
        )

    def test_create_category_prevents_three_levels(self, service, mock_repository, parent_category, child_category, user_id):
        mock_repository.get_by_id.return_value = child_category

        with pytest.raises(
            ValueError,
            match="Cannot create more than 2 levels of categories. Parent category already has a parent.",
        ):
            service.create_category(name="Grandchild Category", user_id=user_id, parent_id=child_category.id)

        mock_repository.get_by_id.assert_called_once_with(child_category.id, user_id)
        mock_repository.create.assert_not_called()

    def test_create_category_allows_two_levels(self, service, mock_repository, parent_category, user_id):
        mock_repository.get_by_id.return_value = parent_category
        expected_category = Category(
            id=uuid4(),
            name="Child Category",
            parent_id=parent_category.id,
            user_id=user_id,
        )
        mock_repository.create.return_value = expected_category

        result = service.create_category(name="Child Category", user_id=user_id, parent_id=parent_category.id)

        assert result == expected_category
        mock_repository.get_by_id.assert_called_once_with(parent_category.id, user_id)
        mock_repository.create.assert_called_once()

    def test_create_category_allows_root_category(self, service, mock_repository, user_id):
        expected_category = Category(
            id=uuid4(),
            name="Root Category",
            parent_id=None,
            user_id=user_id,
        )
        mock_repository.create.return_value = expected_category

        result = service.create_category(name="Root Category", user_id=user_id, parent_id=None)

        assert result == expected_category
        mock_repository.create.assert_called_once()

    def test_update_category_prevents_three_levels(self, service, mock_repository, parent_category, child_category, user_id):
        grandchild_id = uuid4()
        grandchild = Category(
            id=grandchild_id,
            name="Grandchild Category",
            parent_id=None,
            user_id=user_id,
        )
        mock_repository.get_by_id.side_effect = [grandchild, child_category]

        with pytest.raises(
            ValueError,
            match="Cannot create more than 2 levels of categories. Parent category already has a parent.",
        ):
            service.update_category(
                category_id=grandchild_id,
                name="Grandchild Category",
                user_id=user_id,
                parent_id=child_category.id,
            )

        mock_repository.update.assert_not_called()

    def test_update_category_allows_two_levels(self, service, mock_repository, parent_category, user_id):
        child_id = uuid4()
        child = Category(
            id=child_id,
            name="Child Category",
            parent_id=None,
            user_id=user_id,
        )
        mock_repository.get_by_id.side_effect = [child, parent_category]
        updated_child = Category(
            id=child_id,
            name="Updated Child",
            parent_id=parent_category.id,
            user_id=user_id,
        )
        mock_repository.update.return_value = updated_child

        result = service.update_category(
            category_id=child_id,
            name="Updated Child",
            user_id=user_id,
            parent_id=parent_category.id,
        )

        assert result == updated_child
        mock_repository.update.assert_called_once()

    def test_upsert_category_prevents_three_levels(self, service, mock_repository, parent_category, child_category, user_id):
        mock_repository.get_by_id.return_value = child_category

        with pytest.raises(
            ValueError,
            match="Cannot create more than 2 levels of categories. Parent category already has a parent.",
        ):
            service.upsert_category(name="Grandchild Category", user_id=user_id, parent_id=child_category.id)

        mock_repository.get_by_id.assert_called_once_with(child_category.id, user_id)
        mock_repository.get_by_name.assert_not_called()
        mock_repository.create.assert_not_called()

    def test_upsert_category_allows_two_levels(self, service, mock_repository, parent_category, user_id):
        mock_repository.get_by_id.return_value = parent_category
        mock_repository.get_by_name.return_value = None
        expected_category = Category(
            id=uuid4(),
            name="Child Category",
            parent_id=parent_category.id,
            user_id=user_id,
        )
        mock_repository.create.return_value = expected_category

        result = service.upsert_category(name="Child Category", user_id=user_id, parent_id=parent_category.id)

        assert result == expected_category
        mock_repository.get_by_id.assert_called_once_with(parent_category.id, user_id)
        mock_repository.create.assert_called_once()
