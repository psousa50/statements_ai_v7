from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from app.api.schemas import TransactionCreate, TransactionResponse
from app.domain.models.account import Account
from app.domain.models.category import Category
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from tests.api.helpers import TEST_USER_ID, build_client, mocked_dependencies


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
        categorization_status=CategorizationStatus.RULE_BASED,
        sort_index=0,
        source_type=SourceType.MANUAL,
        manual_position_after=None,
    )

    mock_account = Account(id=account_id, name="Test Account", user_id=TEST_USER_ID)
    internal_dependencies.account_service.get_account.return_value = mock_account
    internal_dependencies.transaction_service.create_transaction.return_value = mock_transaction
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
    assert transaction_response.categorization_status == CategorizationStatus.RULE_BASED
    assert transaction_response.created_at is not None
    assert transaction_response.sort_index == 0
    assert transaction_response.source_type == SourceType.MANUAL.value
    assert transaction_response.manual_position_after is None

    internal_dependencies.account_service.get_account.assert_called_once_with(account_id, TEST_USER_ID)
    internal_dependencies.transaction_service.create_transaction.assert_called_once()


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
        sort_index=0,
        source_type=SourceType.MANUAL,
        manual_position_after=None,
    )
    internal_dependencies.transaction_service.get_transaction.return_value = mock_transaction

    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction_id}")
    assert response.status_code == 200
    transaction_response = TransactionResponse.model_validate(response.json())
    assert transaction_response.id == transaction_id
    assert transaction_response.sort_index == 0
    assert transaction_response.source_type == SourceType.MANUAL.value
    assert transaction_response.manual_position_after is None

    internal_dependencies.transaction_service.get_transaction.assert_called_once_with(transaction_id, TEST_USER_ID)


def test_get_transaction_not_found():
    internal_dependencies = mocked_dependencies()
    transaction_id = uuid4()
    internal_dependencies.transaction_service.get_transaction.return_value = None

    client = build_client(internal_dependencies)

    response = client.get(f"/api/v1/transactions/{transaction_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Transaction with ID {transaction_id} not found"

    internal_dependencies.transaction_service.get_transaction.assert_called_once_with(transaction_id, TEST_USER_ID)


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

    internal_dependencies.transaction_service.get_category_totals.return_value = mock_totals
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


def test_preview_enhancement_with_exact_match():
    internal_dependencies = mocked_dependencies()

    category_id = uuid4()
    rule_id = uuid4()

    mock_category = Category(id=category_id, name="Groceries")
    mock_rule = EnhancementRule(
        id=rule_id,
        normalized_description_pattern="tesco",
        match_type=MatchType.EXACT,
        category_id=category_id,
        source=EnhancementRuleSource.MANUAL,
    )

    internal_dependencies.enhancement_rule_repository.find_matching_rules.return_value = [mock_rule]
    internal_dependencies.category_repository.get_by_id.return_value = mock_category

    def mock_apply_rules(transactions, rules):
        transaction = transactions[0]
        transaction.category_id = category_id
        return [transaction]

    internal_dependencies.transaction_enhancer.apply_rules.side_effect = mock_apply_rules

    client = build_client(internal_dependencies)

    request_data = {
        "description": "Tesco Store",
        "amount": "25.50",
        "transaction_date": "2023-01-15",
    }

    response = client.post(
        "/api/v1/transactions/preview-enhancement",
        json=request_data,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["matched"] is True
    assert response_data["rule_pattern"] == "tesco"
    assert response_data["category_id"] == str(category_id)
    assert response_data["category_name"] == "Groceries"
    assert response_data["counterparty_account_id"] is None
    assert response_data["counterparty_account_name"] is None


def test_preview_enhancement_with_prefix_match():
    internal_dependencies = mocked_dependencies()

    category_id = uuid4()
    account_id = uuid4()
    rule_id = uuid4()

    mock_category = Category(id=category_id, name="Transport")
    mock_rule = EnhancementRule(
        id=rule_id,
        normalized_description_pattern="uber",
        match_type=MatchType.PREFIX,
        category_id=category_id,
        source=EnhancementRuleSource.MANUAL,
    )

    internal_dependencies.enhancement_rule_repository.find_matching_rules.return_value = [mock_rule]
    internal_dependencies.category_repository.get_by_id.return_value = mock_category

    def mock_apply_rules(transactions, rules):
        transaction = transactions[0]
        transaction.category_id = category_id
        return [transaction]

    internal_dependencies.transaction_enhancer.apply_rules.side_effect = mock_apply_rules

    client = build_client(internal_dependencies)

    request_data = {
        "description": "Uber Trip London",
        "amount": "12.30",
        "account_id": str(account_id),
    }

    response = client.post(
        "/api/v1/transactions/preview-enhancement",
        json=request_data,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["matched"] is True
    assert response_data["category_id"] == str(category_id)
    assert response_data["category_name"] == "Transport"


def test_preview_enhancement_with_infix_match():
    internal_dependencies = mocked_dependencies()

    category_id = uuid4()
    account_id = uuid4()
    rule_id = uuid4()

    mock_category = Category(id=category_id, name="Dining")
    mock_rule = EnhancementRule(
        id=rule_id,
        normalized_description_pattern="restaurant",
        match_type=MatchType.INFIX,
        category_id=category_id,
        source=EnhancementRuleSource.MANUAL,
    )

    internal_dependencies.enhancement_rule_repository.find_matching_rules.return_value = [mock_rule]
    internal_dependencies.category_repository.get_by_id.return_value = mock_category

    def mock_apply_rules(transactions, rules):
        transaction = transactions[0]
        transaction.category_id = category_id
        return [transaction]

    internal_dependencies.transaction_enhancer.apply_rules.side_effect = mock_apply_rules

    client = build_client(internal_dependencies)

    request_data = {
        "description": "The Best Restaurant in Town",
        "amount": "45.00",
        "account_id": str(account_id),
    }

    response = client.post(
        "/api/v1/transactions/preview-enhancement",
        json=request_data,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["matched"] is True
    assert response_data["category_id"] == str(category_id)
    assert response_data["category_name"] == "Dining"


def test_preview_enhancement_with_counterparty():
    internal_dependencies = mocked_dependencies()

    account_id = uuid4()
    counterparty_account_id = uuid4()
    rule_id = uuid4()

    mock_counterparty = Account(id=counterparty_account_id, name="Savings Account")
    mock_rule = EnhancementRule(
        id=rule_id,
        normalized_description_pattern="transfer to savings",
        match_type=MatchType.EXACT,
        counterparty_account_id=counterparty_account_id,
        source=EnhancementRuleSource.MANUAL,
    )

    internal_dependencies.enhancement_rule_repository.find_matching_rules.return_value = [mock_rule]
    internal_dependencies.account_repository.get_by_id.return_value = mock_counterparty

    def mock_apply_rules(transactions, rules):
        transaction = transactions[0]
        transaction.counterparty_account_id = counterparty_account_id
        return [transaction]

    internal_dependencies.transaction_enhancer.apply_rules.side_effect = mock_apply_rules

    client = build_client(internal_dependencies)

    request_data = {
        "description": "Transfer to Savings",
        "amount": "500.00",
        "account_id": str(account_id),
    }

    response = client.post(
        "/api/v1/transactions/preview-enhancement",
        json=request_data,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["matched"] is True
    assert response_data["category_id"] is None
    assert response_data["category_name"] is None
    assert response_data["counterparty_account_id"] == str(counterparty_account_id)
    assert response_data["counterparty_account_name"] == "Savings Account"


def test_preview_enhancement_with_amount_constraint():
    internal_dependencies = mocked_dependencies()

    category_id = uuid4()
    account_id = uuid4()
    rule_id = uuid4()

    mock_category = Category(id=category_id, name="Large Purchases")
    mock_rule = EnhancementRule(
        id=rule_id,
        normalized_description_pattern="amazon",
        match_type=MatchType.PREFIX,
        category_id=category_id,
        min_amount=Decimal("100.00"),
        source=EnhancementRuleSource.MANUAL,
    )

    internal_dependencies.enhancement_rule_repository.find_matching_rules.return_value = [mock_rule]
    internal_dependencies.category_repository.get_by_id.return_value = mock_category

    def mock_apply_rules(transactions, rules):
        transaction = transactions[0]
        if transaction.amount >= Decimal("100.00"):
            transaction.category_id = category_id
        return [transaction]

    internal_dependencies.transaction_enhancer.apply_rules.side_effect = mock_apply_rules

    client = build_client(internal_dependencies)

    request_data = {
        "description": "Amazon Purchase",
        "amount": "150.00",
        "account_id": str(account_id),
    }

    response = client.post(
        "/api/v1/transactions/preview-enhancement",
        json=request_data,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["matched"] is True
    assert response_data["category_id"] == str(category_id)


def test_preview_enhancement_with_date_constraint():
    internal_dependencies = mocked_dependencies()

    category_id = uuid4()
    account_id = uuid4()
    rule_id = uuid4()

    mock_category = Category(id=category_id, name="Holiday Shopping")
    mock_rule = EnhancementRule(
        id=rule_id,
        normalized_description_pattern="shop",
        match_type=MatchType.INFIX,
        category_id=category_id,
        start_date=date(2023, 12, 1),
        end_date=date(2023, 12, 31),
        source=EnhancementRuleSource.MANUAL,
    )

    internal_dependencies.enhancement_rule_repository.find_matching_rules.return_value = [mock_rule]
    internal_dependencies.category_repository.get_by_id.return_value = mock_category

    def mock_apply_rules(transactions, rules):
        transaction = transactions[0]
        if date(2023, 12, 1) <= transaction.date <= date(2023, 12, 31):
            transaction.category_id = category_id
        return [transaction]

    internal_dependencies.transaction_enhancer.apply_rules.side_effect = mock_apply_rules

    client = build_client(internal_dependencies)

    request_data = {
        "description": "Shop Purchase",
        "amount": "50.00",
        "transaction_date": "2023-12-15",
        "account_id": str(account_id),
    }

    response = client.post(
        "/api/v1/transactions/preview-enhancement",
        json=request_data,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["matched"] is True
    assert response_data["category_id"] == str(category_id)


def test_preview_enhancement_no_match():
    internal_dependencies = mocked_dependencies()

    account_id = uuid4()
    rule_id = uuid4()

    mock_rule = EnhancementRule(
        id=rule_id,
        normalized_description_pattern="tesco",
        match_type=MatchType.EXACT,
        category_id=uuid4(),
        source=EnhancementRuleSource.MANUAL,
    )

    internal_dependencies.enhancement_rule_repository.find_matching_rules.return_value = [mock_rule]

    def mock_apply_rules(transactions, rules):
        return transactions

    internal_dependencies.transaction_enhancer.apply_rules.side_effect = mock_apply_rules

    client = build_client(internal_dependencies)

    request_data = {
        "description": "Random Store",
        "amount": "25.00",
        "account_id": str(account_id),
    }

    response = client.post(
        "/api/v1/transactions/preview-enhancement",
        json=request_data,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["matched"] is False
    assert response_data["rule_pattern"] is None
    assert response_data["category_id"] is None
    assert response_data["category_name"] is None


def test_preview_enhancement_rule_precedence():
    internal_dependencies = mocked_dependencies()

    category_exact_id = uuid4()
    category_prefix_id = uuid4()
    account_id = uuid4()

    mock_category_exact = Category(id=category_exact_id, name="Exact Match Category")

    exact_rule = EnhancementRule(
        id=uuid4(),
        normalized_description_pattern="tesco supermarket",
        match_type=MatchType.EXACT,
        category_id=category_exact_id,
        source=EnhancementRuleSource.MANUAL,
    )

    prefix_rule = EnhancementRule(
        id=uuid4(),
        normalized_description_pattern="tesco",
        match_type=MatchType.PREFIX,
        category_id=category_prefix_id,
        source=EnhancementRuleSource.MANUAL,
    )

    internal_dependencies.enhancement_rule_repository.find_matching_rules.return_value = [prefix_rule, exact_rule]
    internal_dependencies.category_repository.get_by_id.return_value = mock_category_exact

    def mock_apply_rules(transactions, rules):
        transaction = transactions[0]
        transaction.category_id = category_exact_id
        return [transaction]

    internal_dependencies.transaction_enhancer.apply_rules.side_effect = mock_apply_rules

    client = build_client(internal_dependencies)

    request_data = {
        "description": "Tesco Supermarket",
        "amount": "35.00",
        "account_id": str(account_id),
    }

    response = client.post(
        "/api/v1/transactions/preview-enhancement",
        json=request_data,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["matched"] is True
    assert response_data["category_id"] == str(category_exact_id)
    assert response_data["category_name"] == "Exact Match Category"
