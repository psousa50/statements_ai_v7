from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from tests.api.helpers import TEST_USER_ID, build_client, mocked_dependencies


def _make_transaction(**overrides):
    defaults = dict(
        id=uuid4(),
        date=date(2023, 1, 1),
        description="Test transaction",
        normalized_description="test transaction",
        amount=Decimal(100.00),
        created_at=datetime(2023, 1, 1),
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        sort_index=0,
        source_type=SourceType.MANUAL,
        manual_position_after=None,
        exclude_from_analytics=False,
    )
    defaults.update(overrides)
    return Transaction(**defaults)


def test_toggle_exclude_from_analytics_excludes_transaction():
    internal_dependencies = mocked_dependencies()
    transaction = _make_transaction(exclude_from_analytics=True)
    internal_dependencies.transaction_service.toggle_exclude_from_analytics.return_value = transaction
    client = build_client(internal_dependencies)

    response = client.put(
        f"/api/v1/transactions/{transaction.id}/exclude-from-analytics",
        json={"exclude_from_analytics": True},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["exclude_from_analytics"] is True
    internal_dependencies.transaction_service.toggle_exclude_from_analytics.assert_called_once_with(
        transaction_id=transaction.id,
        user_id=TEST_USER_ID,
        exclude_from_analytics=True,
    )


def test_toggle_exclude_from_analytics_includes_transaction():
    internal_dependencies = mocked_dependencies()
    transaction = _make_transaction(exclude_from_analytics=False)
    internal_dependencies.transaction_service.toggle_exclude_from_analytics.return_value = transaction
    client = build_client(internal_dependencies)

    response = client.put(
        f"/api/v1/transactions/{transaction.id}/exclude-from-analytics",
        json={"exclude_from_analytics": False},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["exclude_from_analytics"] is False


def test_toggle_exclude_from_analytics_not_found():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    internal_dependencies.transaction_service.toggle_exclude_from_analytics.return_value = None
    client = build_client(internal_dependencies)

    response = client.put(
        f"/api/v1/transactions/{transaction_id}/exclude-from-analytics",
        json={"exclude_from_analytics": True},
    )

    assert response.status_code == 404


def test_get_transaction_includes_exclude_from_analytics_field():
    internal_dependencies = mocked_dependencies()
    transaction = _make_transaction(exclude_from_analytics=True)
    internal_dependencies.transaction_service.get_transaction.return_value = transaction
    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction.id}")

    assert response.status_code == 200
    response_data = response.json()
    assert "exclude_from_analytics" in response_data
    assert response_data["exclude_from_analytics"] is True


def test_get_transaction_default_exclude_from_analytics_is_false():
    internal_dependencies = mocked_dependencies()
    transaction = _make_transaction()
    internal_dependencies.transaction_service.get_transaction.return_value = transaction
    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction.id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["exclude_from_analytics"] is False


def test_list_transactions_with_exclude_from_analytics_filter():
    internal_dependencies = mocked_dependencies()
    from app.api.schemas import TransactionListResponse

    transaction = _make_transaction(exclude_from_analytics=True)
    mock_response = TransactionListResponse(
        transactions=[transaction],
        total=1,
        page=1,
        page_size=20,
        total_pages=1,
        total_amount=Decimal("100.00"),
    )
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = mock_response
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions?exclude_from_analytics=true")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs[1].get("exclude_from_analytics") is True or call_kwargs.kwargs.get("exclude_from_analytics") is True


def test_category_totals_excludes_analytics_excluded_by_default():
    internal_dependencies = mocked_dependencies()
    category_id = uuid4()
    mock_totals = {
        category_id: {
            "total_amount": Decimal("150.50"),
            "transaction_count": Decimal("3"),
        },
    }
    internal_dependencies.transaction_service.get_category_totals.return_value = mock_totals
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions/category-totals")

    assert response.status_code == 200


def test_category_time_series_excludes_analytics_excluded_by_default():
    internal_dependencies = mocked_dependencies()
    internal_dependencies.transaction_service.get_category_time_series.return_value = []
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions/category-time-series")

    assert response.status_code == 200
