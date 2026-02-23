from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.api.schemas import TransactionListResponse
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from tests.api.helpers import TEST_USER_ID, build_client, mocked_dependencies


def _make_transaction(**overrides):
    defaults = dict(
        id=uuid4(),
        date=date(2023, 1, 1),
        description="Test transaction",
        normalized_description="test transaction",
        amount=Decimal("100.00"),
        created_at=datetime(2023, 1, 1),
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        sort_index=0,
        source_type=SourceType.MANUAL,
        manual_position_after=None,
        exclude_from_analytics=False,
    )
    defaults.update(overrides)
    return Transaction(**defaults)


def _paginated_response(transactions):
    return TransactionListResponse(
        transactions=transactions,
        total=len(transactions),
        page=1,
        page_size=20,
        total_pages=1,
        total_amount=sum(t.amount for t in transactions),
    )


def test_filter_excluded_transactions_only():
    internal_dependencies = mocked_dependencies()
    excluded = _make_transaction(exclude_from_analytics=True, description="Excluded")
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([excluded])
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions?exclude_from_analytics=true")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is True


def test_filter_excluded_false_shows_only_included():
    internal_dependencies = mocked_dependencies()
    included = _make_transaction(exclude_from_analytics=False, description="Included")
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([included])
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions?exclude_from_analytics=false")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is False


def test_no_excluded_filter_passes_none():
    internal_dependencies = mocked_dependencies()
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([])
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is None


def test_excluded_filter_combines_with_category_filter():
    internal_dependencies = mocked_dependencies()
    category_id = uuid4()
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([])
    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions?exclude_from_analytics=true&category_ids={category_id}")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is True
    assert call_kwargs.kwargs.get("category_ids") == [category_id]


def test_excluded_filter_combines_with_date_range():
    internal_dependencies = mocked_dependencies()
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([])
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions?exclude_from_analytics=true&start_date=2023-01-01&end_date=2023-12-31")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is True
    assert call_kwargs.kwargs.get("start_date") == date(2023, 1, 1)
    assert call_kwargs.kwargs.get("end_date") == date(2023, 12, 31)


def test_excluded_filter_combines_with_account_filter():
    internal_dependencies = mocked_dependencies()
    account_id = uuid4()
    from app.domain.models.account import Account

    mock_account = Account(id=account_id, name="Test Account", user_id=TEST_USER_ID)
    internal_dependencies.account_service.get_account.return_value = mock_account
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([])
    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions?exclude_from_analytics=true&account_id={account_id}")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is True
    assert call_kwargs.kwargs.get("account_id") == account_id


def test_excluded_filter_combines_with_description_search():
    internal_dependencies = mocked_dependencies()
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([])
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions?exclude_from_analytics=true&description_search=rent")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is True
    assert call_kwargs.kwargs.get("description_search") == "rent"


def test_excluded_filter_combines_with_amount_range():
    internal_dependencies = mocked_dependencies()
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([])
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions?exclude_from_analytics=true&min_amount=100&max_amount=500")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is True
    assert call_kwargs.kwargs.get("min_amount") == Decimal("100")
    assert call_kwargs.kwargs.get("max_amount") == Decimal("500")


def test_excluded_filter_combines_with_tag_filter():
    internal_dependencies = mocked_dependencies()
    tag_id = uuid4()
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response([])
    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions?exclude_from_analytics=true&tag_ids={tag_id}")

    assert response.status_code == 200
    call_kwargs = internal_dependencies.transaction_service.get_transactions_paginated.call_args
    assert call_kwargs.kwargs.get("exclude_from_analytics") is True
    assert call_kwargs.kwargs.get("tag_ids") == [tag_id]


def test_excluded_filter_response_contains_only_excluded_transactions():
    internal_dependencies = mocked_dependencies()
    excluded_transaction = _make_transaction(exclude_from_analytics=True, description="Excluded")
    internal_dependencies.transaction_service.get_transactions_paginated.return_value = _paginated_response(
        [excluded_transaction]
    )
    client = build_client(internal_dependencies)

    response = client.get("/api/v1/transactions?exclude_from_analytics=true")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["transactions"][0]["exclude_from_analytics"] is True
