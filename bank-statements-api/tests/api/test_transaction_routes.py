from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from tests.api.helpers import build_client, mocked_dependencies
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.api.schemas import TransactionCreate, TransactionResponse
from fastapi.encoders import jsonable_encoder


def test_create_transaction():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    category_id = uuid4()
    mock_transaction = Transaction(
        id=transaction_id,
        date=date(2023, 1, 1),
        description="Test transaction",
        amount=Decimal(100.00),
        created_at=datetime(2023, 1, 1),
        category_id=category_id,
        categorization_status=CategorizationStatus.CATEGORIZED,
    )

    internal_dependencies.transaction_service.create_transaction.return_value = mock_transaction
    client = build_client(internal_dependencies)

    transaction_data = TransactionCreate(
        date=date(2023, 1, 1),
        description="Test transaction",
        amount=Decimal(100.00),
        category_id=category_id,
    )
    response = client.post(
        "/api/v1/transactions",
        json=jsonable_encoder(transaction_data),
    )

    transaction_response = TransactionResponse.model_validate(response.json())

    assert response.status_code == 201
    assert transaction_response.id == transaction_id
    assert transaction_response.date == date(2023, 1, 1)
    assert transaction_response.description == "Test transaction"
    assert transaction_response.amount == Decimal(100.00)
    assert transaction_response.category_id == category_id
    assert transaction_response.categorization_status == CategorizationStatus.CATEGORIZED
    assert transaction_response.created_at is not None

    internal_dependencies.transaction_service.create_transaction.assert_called_once_with(
        transaction_date=date(2023, 1, 1),
        description="Test transaction",
        amount=Decimal(100.00),
        category_id=category_id,
    )

    assert response.status_code == 201
    assert transaction_response.id == transaction_id

    internal_dependencies.transaction_service.create_transaction.assert_called_once_with(
        transaction_date=date(2023, 1, 1),
        description="Test transaction",
        amount=Decimal(100.00),
        category_id=category_id,
    )


def test_get_transaction():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    mock_transaction = Transaction(
        id=transaction_id,
        date=date(2023, 1, 1),
        description="Test transaction",
        amount=Decimal(100.00),
        created_at=date(2023, 1, 1),
        categorization_status=CategorizationStatus.UNCATEGORIZED,
    )
    internal_dependencies.transaction_service.get_transaction.return_value = mock_transaction

    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction_id}")
    transaction_response = TransactionResponse.model_validate(response.json())

    assert response.status_code == 200
    assert transaction_response.id == transaction_id
    assert transaction_response.date == date(2023, 1, 1)
    assert transaction_response.description == "Test transaction"
    assert transaction_response.amount == Decimal(100.00)
    assert transaction_response.category_id is None
    assert transaction_response.categorization_status == CategorizationStatus.UNCATEGORIZED
    assert transaction_response.created_at is not None

    internal_dependencies.transaction_service.get_transaction.assert_called_once_with(transaction_id)


def test_get_transaction_not_found():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    internal_dependencies.transaction_service.get_transaction.return_value = None

    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction_id}")
    assert response.status_code == 404

    internal_dependencies.transaction_service.get_transaction.assert_called_once_with(transaction_id)

    assert "not found" in response.json()["detail"]
