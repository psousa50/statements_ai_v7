from typing import Iterator
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.categories import register_category_routes
from app.core.dependencies import InternalDependencies
from app.domain.models.category import Category


@pytest.fixture
def mock_category_service():
    """Create a mock category service."""
    return MagicMock()


@pytest.fixture
def mock_transaction_service():
    """Create a mock transaction service."""
    return MagicMock()


@pytest.fixture
def mock_provide_dependencies(mock_category_service, mock_transaction_service):
    """Create a mock dependency provider function."""
    mock_statement_analyzer_service = MagicMock()
    mock_statement_persistence_service = MagicMock()
    mock_source_service = MagicMock()

    internal = InternalDependencies(
        category_service=mock_category_service,
        transaction_service=mock_transaction_service,
        source_service=mock_source_service,
        statement_analyzer_service=mock_statement_analyzer_service,
        statement_persistence_service=mock_statement_persistence_service,
    )

    def _provide_dependencies() -> Iterator[InternalDependencies]:
        yield internal

    return _provide_dependencies


@pytest.fixture
def test_app(mock_provide_dependencies):
    """Create a test app with mocked dependencies."""
    app = FastAPI()
    register_category_routes(app, mock_provide_dependencies)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


def test_create_category(client, mock_category_service):
    """Test creating a category."""
    # Setup mock
    category_id = uuid4()
    mock_category = Category(
        id=category_id,
        name="Test Category",
    )
    mock_category_service.create_category.return_value = mock_category

    # Make request
    response = client.post(
        "/api/v1/categories",
        json={
            "name": "Test Category",
        },
    )

    # Assert response
    assert response.status_code == 201
    assert response.json()["id"] == str(category_id)
    assert response.json()["name"] == "Test Category"

    # Assert mock was called correctly
    mock_category_service.create_category.assert_called_once_with(
        name="Test Category",
        parent_id=None,
    )


def test_create_subcategory(client, mock_category_service):
    """Test creating a subcategory."""
    # Setup mock
    category_id = uuid4()
    parent_id = uuid4()
    mock_category = Category(
        id=category_id,
        name="Test Subcategory",
        parent_id=parent_id,
    )
    mock_category_service.create_category.return_value = mock_category

    # Make request
    response = client.post(
        "/api/v1/categories",
        json={
            "name": "Test Subcategory",
            "parent_id": str(parent_id),
        },
    )

    # Assert response
    assert response.status_code == 201
    assert response.json()["id"] == str(category_id)
    assert response.json()["name"] == "Test Subcategory"
    assert response.json()["parent_id"] == str(parent_id)

    # Assert mock was called correctly
    mock_category_service.create_category.assert_called_once_with(
        name="Test Subcategory",
        parent_id=parent_id,
    )


def test_get_categories(client, mock_category_service):
    """Test getting all categories."""
    # Setup mock
    category_id1 = uuid4()
    category_id2 = uuid4()
    mock_categories = [
        Category(id=category_id1, name="Category 1"),
        Category(id=category_id2, name="Category 2"),
    ]
    mock_category_service.get_all_categories.return_value = mock_categories

    # Make request
    response = client.get("/api/v1/categories")

    # Assert response
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["categories"]) == 2
    assert response.json()["categories"][0]["id"] == str(category_id1)
    assert response.json()["categories"][1]["id"] == str(category_id2)

    # Assert mock was called correctly
    mock_category_service.get_all_categories.assert_called_once()


def test_get_root_categories(client, mock_category_service):
    """Test getting root categories."""
    # Setup mock
    category_id1 = uuid4()
    category_id2 = uuid4()
    mock_categories = [
        Category(id=category_id1, name="Root Category 1"),
        Category(id=category_id2, name="Root Category 2"),
    ]
    mock_category_service.get_root_categories.return_value = mock_categories

    # Make request
    response = client.get("/api/v1/categories/root")

    # Assert response
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["categories"]) == 2
    assert response.json()["categories"][0]["id"] == str(category_id1)
    assert response.json()["categories"][1]["id"] == str(category_id2)

    # Assert mock was called correctly
    mock_category_service.get_root_categories.assert_called_once()


def test_get_subcategories(client, mock_category_service):
    """Test getting subcategories."""
    # Setup mock
    parent_id = uuid4()
    subcategory_id1 = uuid4()
    subcategory_id2 = uuid4()
    mock_subcategories = [
        Category(id=subcategory_id1, name="Subcategory 1", parent_id=parent_id),
        Category(id=subcategory_id2, name="Subcategory 2", parent_id=parent_id),
    ]
    mock_category_service.get_subcategories.return_value = mock_subcategories

    # Make request
    response = client.get(f"/api/v1/categories/{parent_id}/subcategories")

    # Assert response
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["categories"]) == 2
    assert response.json()["categories"][0]["id"] == str(subcategory_id1)
    assert response.json()["categories"][1]["id"] == str(subcategory_id2)

    # Assert mock was called correctly
    mock_category_service.get_subcategories.assert_called_once_with(parent_id)


def test_update_category(client, mock_category_service):
    """Test updating a category."""
    # Setup mock
    category_id = uuid4()
    mock_category = Category(
        id=category_id,
        name="Updated Category",
    )
    mock_category_service.update_category.return_value = mock_category

    # Make request
    response = client.put(
        f"/api/v1/categories/{category_id}",
        json={
            "name": "Updated Category",
        },
    )

    # Assert response
    assert response.status_code == 200
    assert response.json()["id"] == str(category_id)
    assert response.json()["name"] == "Updated Category"

    # Assert mock was called correctly
    mock_category_service.update_category.assert_called_once_with(
        category_id=category_id,
        name="Updated Category",
        parent_id=None,
    )


def test_delete_category(client, mock_category_service):
    """Test deleting a category."""
    # Setup mock
    category_id = uuid4()
    mock_category_service.delete_category.return_value = True

    # Make request
    response = client.delete(f"/api/v1/categories/{category_id}")

    # Assert response
    assert response.status_code == 204

    # Assert mock was called correctly
    mock_category_service.delete_category.assert_called_once_with(category_id)


def test_delete_category_not_found(client, mock_category_service):
    """Test deleting a category that doesn't exist."""
    # Setup mock
    category_id = uuid4()
    mock_category_service.delete_category.return_value = False

    # Make request
    response = client.delete(f"/api/v1/categories/{category_id}")

    # Assert response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
