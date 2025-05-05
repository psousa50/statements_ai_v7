from datetime import date
from decimal import Decimal
from typing import Iterator
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.transactions import register_transaction_routes
from app.core.dependencies import InternalDependencies
from app.domain.models.transaction import CategorizationStatus, Transaction


@pytest.fixture
def mock_transaction_service():
    """Create a mock transaction service."""
    return MagicMock()


@pytest.fixture
def mock_category_service():
    """Create a mock category service."""
    return MagicMock()


@pytest.fixture
def mock_provide_dependencies(mock_transaction_service):
    """Create a mock dependency provider function."""
    mock_category_service = MagicMock()
    mock_statement_analyzer_service = MagicMock()
    mock_statement_persistence_service = MagicMock()

    internal = InternalDependencies(
        transaction_service=mock_transaction_service,
        category_service=mock_category_service,
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
    register_transaction_routes(app, mock_provide_dependencies)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


def test_create_transaction(client, mock_transaction_service):
    """Test creating a transaction."""
    # Setup mock
    transaction_id = uuid4()
    category_id = uuid4()
    mock_transaction = Transaction(
        id=transaction_id,
        date="2023-01-01",
        description="Test transaction",
        amount=100.00,
        created_at="2023-01-01",
        category_id=category_id,
        categorization_status=CategorizationStatus.CATEGORIZED,
    )
    mock_transaction_service.create_transaction.return_value = mock_transaction

    # Make request
    response = client.post(
        "/api/v1/transactions",
        json={
            "date": "2023-01-01",
            "description": "Test transaction",
            "amount": 100.00,
            "category_id": str(category_id),
        },
    )

    # Assert response
    assert response.status_code == 201
    assert response.json()["id"] == str(transaction_id)

    # Assert mock was called correctly
    mock_transaction_service.create_transaction.assert_called_once_with(
        transaction_date=date(2023, 1, 1),
        description="Test transaction",
        amount=Decimal(100.00),
        category_id=category_id,
    )


def test_get_transaction(client, mock_transaction_service):
    """Test getting a transaction."""
    # Setup mock
    transaction_id = uuid4()
    mock_transaction = Transaction(
        id=transaction_id,
        date="2023-01-01",
        description="Test transaction",
        amount=100.00,
        created_at="2023-01-01",
        categorization_status=CategorizationStatus.UNCATEGORIZED,
    )
    mock_transaction_service.get_transaction.return_value = mock_transaction

    # Make request
    response = client.get(f"/api/v1/transactions/{transaction_id}")

    # Assert response
    assert response.status_code == 200
    assert response.json()["id"] == str(transaction_id)

    # Assert mock was called correctly
    mock_transaction_service.get_transaction.assert_called_once_with(transaction_id)


def test_get_transaction_not_found(client, mock_transaction_service):
    """Test getting a transaction that doesn't exist."""
    # Setup mock
    transaction_id = uuid4()
    mock_transaction_service.get_transaction.return_value = None

    # Make request
    response = client.get(f"/api/v1/transactions/{transaction_id}")

    # Assert response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
