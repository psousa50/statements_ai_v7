from uuid import uuid4

from app.domain.models.account import Account
from tests.api.helpers import TEST_USER_ID, build_client, mocked_dependencies


def test_export_accounts():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    account1_id = uuid4()
    account2_id = uuid4()
    mock_accounts = [
        Account(id=account1_id, name="Current Account", user_id=TEST_USER_ID, currency="GBP"),
        Account(id=account2_id, name="Savings Account", user_id=TEST_USER_ID, currency="EUR"),
    ]
    internal_dependencies.account_service.get_all_accounts.return_value = mock_accounts

    response = client.get("/api/v1/accounts/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "accounts-" in response.headers["content-disposition"]

    content = response.text
    lines = content.strip().split("\n")
    assert lines[0] == "name,currency"
    assert lines[1] == "Current Account,GBP"
    assert lines[2] == "Savings Account,EUR"

    internal_dependencies.account_service.get_all_accounts.assert_called_once_with(TEST_USER_ID)


def test_export_accounts_with_special_characters():
    internal_dependencies = mocked_dependencies()
    client = build_client(internal_dependencies)
    account_id = uuid4()
    mock_accounts = [
        Account(id=account_id, name='Account with "quotes" and, commas', user_id=TEST_USER_ID, currency="USD"),
    ]
    internal_dependencies.account_service.get_all_accounts.return_value = mock_accounts

    response = client.get("/api/v1/accounts/export")

    assert response.status_code == 200
    content = response.text
    lines = content.strip().split("\n")
    assert lines[0] == "name,currency"
    assert lines[1] == '"Account with ""quotes"" and, commas",USD'
