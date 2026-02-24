from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from tests.api.helpers import TEST_USER_ID, build_client, mocked_dependencies


def _make_transaction(**overrides):
    defaults = dict(
        id=uuid4(),
        date=date(2024, 3, 10),
        description="Supermarket Shop",
        normalized_description="supermarket shop",
        amount=Decimal("100.00"),
        created_at=datetime(2024, 3, 10),
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        sort_index=0,
        source_type=SourceType.UPLOAD,
        manual_position_after=None,
        exclude_from_analytics=False,
        row_index=0,
        statement_id=uuid4(),
        account_id=uuid4(),
        user_id=TEST_USER_ID,
    )
    defaults.update(overrides)
    return Transaction(**defaults)


def test_split_transaction_returns_200_on_valid_split():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    child_a = _make_transaction(
        amount=Decimal("60.00"),
        description="Part A",
        parent_transaction_id=parent.id,
    )
    child_b = _make_transaction(
        amount=Decimal("40.00"),
        description="Part B",
        parent_transaction_id=parent.id,
    )
    internal_dependencies.transaction_service.split_transaction.return_value = [child_a, child_b]
    client = build_client(internal_dependencies)

    response = client.post(
        f"/api/v1/transactions/{parent.id}/split",
        json={
            "parts": [
                {"amount": "60.00", "description": "Part A"},
                {"amount": "40.00", "description": "Part B"},
            ]
        },
    )

    assert response.status_code == 200


def test_split_transaction_calls_service_with_correct_arguments():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    category_id = uuid4()
    child_a = _make_transaction(
        amount=Decimal("60.00"),
        description="Groceries",
        parent_transaction_id=parent.id,
    )
    child_b = _make_transaction(
        amount=Decimal("40.00"),
        description="Household",
        parent_transaction_id=parent.id,
    )
    internal_dependencies.transaction_service.split_transaction.return_value = [child_a, child_b]
    client = build_client(internal_dependencies)

    client.post(
        f"/api/v1/transactions/{parent.id}/split",
        json={
            "parts": [
                {"amount": "60.00", "description": "Groceries", "category_id": str(category_id)},
                {"amount": "40.00", "description": "Household"},
            ]
        },
    )

    internal_dependencies.transaction_service.split_transaction.assert_called_once()
    call_kwargs = internal_dependencies.transaction_service.split_transaction.call_args
    assert call_kwargs.kwargs["transaction_id"] == parent.id
    assert call_kwargs.kwargs["user_id"] == TEST_USER_ID


def test_split_transaction_response_contains_children():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    child_a = _make_transaction(
        amount=Decimal("60.00"),
        description="Part A",
        parent_transaction_id=parent.id,
    )
    child_b = _make_transaction(
        amount=Decimal("40.00"),
        description="Part B",
        parent_transaction_id=parent.id,
    )
    internal_dependencies.transaction_service.split_transaction.return_value = [child_a, child_b]
    client = build_client(internal_dependencies)

    response = client.post(
        f"/api/v1/transactions/{parent.id}/split",
        json={
            "parts": [
                {"amount": "60.00", "description": "Part A"},
                {"amount": "40.00", "description": "Part B"},
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_split_transaction_returns_404_when_transaction_not_found():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    internal_dependencies.transaction_service.split_transaction.return_value = None
    client = build_client(internal_dependencies)

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/split",
        json={
            "parts": [
                {"amount": "50.00", "description": "Part A"},
                {"amount": "50.00", "description": "Part B"},
            ]
        },
    )

    assert response.status_code == 404


def test_split_transaction_returns_422_when_amounts_do_not_sum_correctly():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    internal_dependencies.transaction_service.split_transaction.side_effect = ValueError("Parts do not sum to parent amount")
    client = build_client(internal_dependencies)

    response = client.post(
        f"/api/v1/transactions/{parent.id}/split",
        json={
            "parts": [
                {"amount": "60.00", "description": "Part A"},
                {"amount": "30.00", "description": "Part B"},
            ]
        },
    )

    assert response.status_code in (400, 422)


def test_split_transaction_returns_409_when_already_split():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))

    from app.services.transaction import TransactionSplitConflictError

    internal_dependencies.transaction_service.split_transaction.side_effect = TransactionSplitConflictError(
        "Transaction already has split children"
    )
    client = build_client(internal_dependencies)

    response = client.post(
        f"/api/v1/transactions/{parent.id}/split",
        json={
            "parts": [
                {"amount": "50.00", "description": "Part A"},
                {"amount": "50.00", "description": "Part B"},
            ]
        },
    )

    assert response.status_code == 409


def test_split_transaction_returns_409_when_splitting_a_child():
    internal_dependencies = mocked_dependencies()
    child = _make_transaction(
        amount=Decimal("50.00"),
        parent_transaction_id=uuid4(),
    )

    from app.services.transaction import TransactionSplitConflictError

    internal_dependencies.transaction_service.split_transaction.side_effect = TransactionSplitConflictError(
        "Cannot split a child transaction"
    )
    client = build_client(internal_dependencies)

    response = client.post(
        f"/api/v1/transactions/{child.id}/split",
        json={
            "parts": [
                {"amount": "25.00", "description": "Sub A"},
                {"amount": "25.00", "description": "Sub B"},
            ]
        },
    )

    assert response.status_code == 409


def test_transaction_response_includes_is_split_parent_field():
    internal_dependencies = mocked_dependencies()
    transaction = _make_transaction()
    transaction.is_split_parent = True
    internal_dependencies.transaction_service.get_transaction.return_value = transaction
    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction.id}")

    assert response.status_code == 200
    response_data = response.json()
    assert "is_split_parent" in response_data


def test_transaction_response_includes_is_split_child_field():
    internal_dependencies = mocked_dependencies()
    transaction = _make_transaction(parent_transaction_id=uuid4())
    transaction.is_split_parent = False
    internal_dependencies.transaction_service.get_transaction.return_value = transaction
    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction.id}")

    assert response.status_code == 200
    response_data = response.json()
    assert "is_split_child" in response_data


def test_transaction_response_includes_parent_transaction_id_field():
    internal_dependencies = mocked_dependencies()
    parent_id = uuid4()
    transaction = _make_transaction(parent_transaction_id=parent_id)
    internal_dependencies.transaction_service.get_transaction.return_value = transaction
    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction.id}")

    assert response.status_code == 200
    response_data = response.json()
    assert "parent_transaction_id" in response_data
    assert response_data["parent_transaction_id"] == str(parent_id)


def test_split_requires_at_least_two_parts():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    client = build_client(internal_dependencies)

    response = client.post(
        f"/api/v1/transactions/{parent.id}/split",
        json={
            "parts": [
                {"amount": "100.00", "description": "Only one part"},
            ]
        },
    )

    assert response.status_code == 422


def test_delete_split_returns_200_on_success():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    parent.is_split_parent = False
    internal_dependencies.transaction_service.unsplit_transaction.return_value = parent
    client = build_client(internal_dependencies)

    response = client.delete(f"/api/v1/transactions/{parent.id}/split")

    assert response.status_code == 200


def test_delete_split_calls_service_with_correct_arguments():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    parent.is_split_parent = False
    internal_dependencies.transaction_service.unsplit_transaction.return_value = parent
    client = build_client(internal_dependencies)

    client.delete(f"/api/v1/transactions/{parent.id}/split")

    internal_dependencies.transaction_service.unsplit_transaction.assert_called_once()
    call_kwargs = internal_dependencies.transaction_service.unsplit_transaction.call_args
    assert call_kwargs.kwargs["transaction_id"] == parent.id
    assert call_kwargs.kwargs["user_id"] == TEST_USER_ID


def test_delete_split_returns_transaction_with_is_split_parent_false():
    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    parent.is_split_parent = False
    internal_dependencies.transaction_service.unsplit_transaction.return_value = parent
    client = build_client(internal_dependencies)

    response = client.delete(f"/api/v1/transactions/{parent.id}/split")

    assert response.status_code == 200
    data = response.json()
    assert data["is_split_parent"] is False


def test_delete_split_returns_404_when_transaction_not_found():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    internal_dependencies.transaction_service.unsplit_transaction.return_value = None
    client = build_client(internal_dependencies)

    response = client.delete(f"/api/v1/transactions/{transaction_id}/split")

    assert response.status_code == 404


def test_delete_split_returns_409_when_transaction_is_not_a_split_parent():
    from app.services.transaction import TransactionSplitConflictError

    internal_dependencies = mocked_dependencies()
    parent = _make_transaction(amount=Decimal("100.00"))
    internal_dependencies.transaction_service.unsplit_transaction.side_effect = TransactionSplitConflictError(
        "Transaction is not a split parent"
    )
    client = build_client(internal_dependencies)

    response = client.delete(f"/api/v1/transactions/{parent.id}/split")

    assert response.status_code == 409
