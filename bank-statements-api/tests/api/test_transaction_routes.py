from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.api.schemas import TransactionCreate, TransactionResponse
from app.domain.models.transaction import (
    CategorizationStatus,
    CounterpartyStatus,
    SourceType,
    Transaction,
)
from fastapi.encoders import jsonable_encoder

from tests.api.helpers import build_client, mocked_dependencies


def test_create_transaction():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    category_id = uuid4()
    account_id = uuid4()
    mock_transaction = Transaction(
        id=transaction_id,
        date=date(2023, 1, 1),
        description="Test transaction",
        normalized_description="test transaction",
        amount=Decimal(100.00),
        created_at=datetime(2023, 1, 1),
        category_id=category_id,
        account_id=account_id,
        categorization_status=CategorizationStatus.CATEGORIZED,
        counterparty_status=CounterpartyStatus.UNPROCESSED,
        sort_index=0,
        source_type=SourceType.MANUAL,
        manual_position_after=None,
    )

    # Patch the correct method for manual transaction creation
    internal_dependencies.transaction_service.create_manual_transaction.return_value = (
        mock_transaction
    )
    client = build_client(internal_dependencies)

    transaction_data = TransactionCreate(
        date=date(2023, 1, 1),
        description="Test transaction",
        amount=Decimal(100.00),
        category_id=category_id,
        account_id=account_id,
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
    assert (
        transaction_response.categorization_status == CategorizationStatus.CATEGORIZED
    )
    assert transaction_response.counterparty_status == CounterpartyStatus.UNPROCESSED
    assert transaction_response.created_at is not None
    assert transaction_response.sort_index == 0
    assert transaction_response.source_type == SourceType.MANUAL.value
    assert transaction_response.manual_position_after is None

    internal_dependencies.transaction_service.create_manual_transaction.assert_called_once()


def test_get_transaction():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    mock_transaction = Transaction(
        id=transaction_id,
        date=date(2023, 1, 1),
        description="Test transaction",
        normalized_description="test transaction",
        amount=Decimal(100.00),
        created_at=date(2023, 1, 1),
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        counterparty_status=CounterpartyStatus.UNPROCESSED,
        sort_index=0,
        source_type=SourceType.MANUAL,
        manual_position_after=None,
    )
    internal_dependencies.transaction_service.get_transaction.return_value = (
        mock_transaction
    )

    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction_id}")
    assert response.status_code == 200
    transaction_response = TransactionResponse.model_validate(response.json())
    assert transaction_response.id == transaction_id
    assert transaction_response.counterparty_status == CounterpartyStatus.UNPROCESSED
    assert transaction_response.sort_index == 0
    assert transaction_response.source_type == SourceType.MANUAL.value
    assert transaction_response.manual_position_after is None

    internal_dependencies.transaction_service.get_transaction.assert_called_once_with(
        transaction_id
    )


def test_get_transaction_not_found():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    internal_dependencies.transaction_service.get_transaction.return_value = None

    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction_id}")

    assert response.status_code == 404
    assert (
        response.json()["detail"] == f"Transaction with ID {transaction_id} not found"
    )

    internal_dependencies.transaction_service.get_transaction.assert_called_once_with(
        transaction_id
    )


def test_get_category_totals():
    internal_dependencies = mocked_dependencies()
    category_id_1 = uuid4()
    category_id_2 = uuid4()

    # Mock the category totals response
    mock_totals = {
        category_id_1: {
            "total_amount": Decimal("150.50"),
            "transaction_count": Decimal("3"),
        },
        category_id_2: {
            "total_amount": Decimal("75.25"),
            "transaction_count": Decimal("2"),
        },
        None: {  # uncategorized
            "total_amount": Decimal("25.00"),
            "transaction_count": Decimal("1"),
        },
    }

    internal_dependencies.transaction_service.get_category_totals.return_value = (
        mock_totals
    )
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions/category-totals")

    assert response.status_code == 200
    response_data = response.json()

    assert "totals" in response_data
    totals = response_data["totals"]
    assert len(totals) == 3

    # Find the specific totals by category_id
    totals_by_id = {total["category_id"]: total for total in totals}

    assert str(category_id_1) in totals_by_id
    assert totals_by_id[str(category_id_1)]["total_amount"] == 150.50
    assert totals_by_id[str(category_id_1)]["transaction_count"] == 3

    assert str(category_id_2) in totals_by_id
    assert totals_by_id[str(category_id_2)]["total_amount"] == 75.25
    assert totals_by_id[str(category_id_2)]["transaction_count"] == 2

    assert None in totals_by_id  # uncategorized
    assert totals_by_id[None]["total_amount"] == 25.00
    assert totals_by_id[None]["transaction_count"] == 1

    internal_dependencies.transaction_service.get_category_totals.assert_called_once()
