from uuid import uuid4

from app.api.schemas import CategoryListResponse, CategoryResponse
from app.domain.models.category import Category
from tests.api.helpers import TEST_USER_ID, build_client, mocked_dependencies


def test_create_category():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    category_id = uuid4()
    mock_category = Category(
        id=category_id,
        name="Test Category",
    )
    internal_dependencies.category_service.create_category.return_value = mock_category

    response = client.post(
        "/api/v1/categories",
        json={
            "name": "Test Category",
        },
    )

    category_response = CategoryResponse.model_validate(response.json())

    assert response.status_code == 201
    assert category_response.id == category_id
    assert category_response.name == "Test Category"
    internal_dependencies.category_service.create_category.assert_called_once_with(
        name="Test Category",
        user_id=TEST_USER_ID,
        parent_id=None,
        color=None,
    )


def test_get_categories():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    category_id1 = uuid4()
    category_id2 = uuid4()
    mock_categories = [
        Category(id=category_id1, name="Category 1"),
        Category(id=category_id2, name="Category 2"),
    ]
    internal_dependencies.category_service.get_all_categories.return_value = mock_categories

    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["categories"]) == 2
    assert response.json()["categories"][0]["id"] == str(category_id1)
    assert response.json()["categories"][1]["id"] == str(category_id2)

    internal_dependencies.category_service.get_all_categories.assert_called_once_with(TEST_USER_ID)


def test_get_root_categories():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    category_id1 = uuid4()
    category_id2 = uuid4()
    mock_categories = [
        Category(id=category_id1, name="Root Category 1"),
        Category(id=category_id2, name="Root Category 2"),
    ]
    internal_dependencies.category_service.get_root_categories.return_value = mock_categories

    response = client.get("/api/v1/categories/root")

    root_categories_response = CategoryListResponse.model_validate(response.json())

    assert response.status_code == 200
    assert root_categories_response.total == 2
    assert len(root_categories_response.categories) == 2
    assert root_categories_response.categories[0].id == category_id1
    assert root_categories_response.categories[1].id == category_id2

    internal_dependencies.category_service.get_root_categories.assert_called_once_with(TEST_USER_ID)


def test_update_category():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    category_id = uuid4()
    mock_category = Category(
        id=category_id,
        name="Updated Category",
    )
    internal_dependencies.category_service.update_category.return_value = mock_category

    response = client.put(
        f"/api/v1/categories/{category_id}",
        json={
            "name": "Updated Category",
        },
    )

    updated_category_response = CategoryResponse.model_validate(response.json())

    assert response.status_code == 200
    assert updated_category_response.id == category_id
    assert updated_category_response.name == "Updated Category"

    internal_dependencies.category_service.update_category.assert_called_once_with(
        category_id=category_id,
        name="Updated Category",
        user_id=TEST_USER_ID,
        parent_id=None,
        color=None,
    )


def test_delete_category():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    category_id = uuid4()
    internal_dependencies.category_service.delete_category.return_value = True

    response = client.delete(f"/api/v1/categories/{category_id}")

    assert response.status_code == 204

    internal_dependencies.category_service.delete_category.assert_called_once_with(category_id, TEST_USER_ID)


def test_delete_category_not_found():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    category_id = uuid4()
    internal_dependencies.category_service.delete_category.return_value = False

    response = client.delete(f"/api/v1/categories/{category_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

    internal_dependencies.category_service.delete_category.assert_called_once_with(category_id, TEST_USER_ID)


def test_get_subcategories():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    parent_id = uuid4()
    subcategory_id1 = uuid4()
    subcategory_id2 = uuid4()
    mock_subcategories = [
        Category(
            id=subcategory_id1,
            name="Subcategory 1",
            parent_id=parent_id,
        ),
        Category(
            id=subcategory_id2,
            name="Subcategory 2",
            parent_id=parent_id,
        ),
    ]
    internal_dependencies.category_service.get_subcategories.return_value = mock_subcategories

    response = client.get(f"/api/v1/categories/{parent_id}/subcategories")

    subcategories_response = CategoryListResponse.model_validate(response.json())

    assert response.status_code == 200
    assert subcategories_response.total == 2
    assert len(subcategories_response.categories) == 2
    assert subcategories_response.categories[0].id == subcategory_id1
    assert subcategories_response.categories[1].id == subcategory_id2

    internal_dependencies.category_service.get_subcategories.assert_called_once_with(parent_id, TEST_USER_ID)


def test_export_categories():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    parent_id = uuid4()
    subcategory_id = uuid4()
    mock_categories = [
        Category(id=parent_id, name="Parent Category", parent_id=None, color="#FF5733"),
        Category(id=subcategory_id, name="Subcategory", parent_id=parent_id, color="#33FF57"),
    ]
    internal_dependencies.category_service.get_all_categories.return_value = mock_categories

    response = client.get("/api/v1/categories/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "categories-" in response.headers["content-disposition"]

    content = response.text
    lines = content.strip().split("\n")
    assert lines[0] == "parent_name,name,color"
    assert lines[1] == ",Parent Category,#FF5733"
    assert lines[2] == "Parent Category,Subcategory,#33FF57"

    internal_dependencies.category_service.get_all_categories.assert_called_once_with(TEST_USER_ID)
