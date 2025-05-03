from decimal import Decimal
from datetime import datetime, date
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.transactions import register_transaction_routes
from app.core.dependencies import InternalDependencies
from app.domain.models.transaction import Transaction


@pytest.fixture
def mock_transaction_service():
    """Create a mock transaction service."""
    return MagicMock()


@pytest.fixture
def test_app(mock_transaction_service):
    """Create a test app with mocked dependencies."""
    app = FastAPI()
    internal = InternalDependencies(transaction_service=mock_transaction_service)
    register_transaction_routes(app, internal)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


def test_create_transaction(client, mock_transaction_service):
    """Test creating a transaction."""
    # Setup mock
    transaction_id = uuid4()
    mock_transaction = Transaction(
        id=transaction_id,
        date="2023-01-01",
        description="Test transaction",
        amount=100.00,
        created_at="2023-01-01",
    )
    mock_transaction_service.create_transaction.return_value = mock_transaction

    # Make request
    response = client.post(
        "/api/v1/transactions",
        json={
            "date": "2023-01-01",
            "description": "Test transaction",
            "amount": 100.00,
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
