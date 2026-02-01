from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.api.errors import ValidationError
from app.domain.models.account import Account
from app.ports.repositories.account import AccountRepository
from app.services.account import AccountService


class TestAccountService:

    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_repository(self):
        repository = MagicMock(spec=AccountRepository)
        return repository

    @pytest.fixture
    def service(self, mock_repository):
        return AccountService(mock_repository)

    @pytest.fixture
    def sample_account(self, user_id):
        account = Account(
            id=uuid4(),
            name="Test Account",
            user_id=user_id,
        )
        return account

    def test_create_account(self, service, mock_repository, sample_account, user_id):
        mock_repository.create.return_value = sample_account
        name = "Test Account"

        result = service.create_account(name=name, user_id=user_id)

        assert result == sample_account
        mock_repository.create.assert_called_once()
        created_account = mock_repository.create.call_args[0][0]
        assert created_account.name == name
        assert created_account.user_id == user_id

    def test_get_account(self, service, mock_repository, sample_account, user_id):
        account_id = sample_account.id
        mock_repository.get_by_id.return_value = sample_account

        result = service.get_account(account_id, user_id)

        assert result == sample_account
        mock_repository.get_by_id.assert_called_once_with(account_id, user_id)

    def test_get_account_not_found(self, service, mock_repository, user_id):
        account_id = uuid4()
        mock_repository.get_by_id.return_value = None

        result = service.get_account(account_id, user_id)

        assert result is None
        mock_repository.get_by_id.assert_called_once_with(account_id, user_id)

    def test_get_account_by_name(self, service, mock_repository, sample_account, user_id):
        name = sample_account.name
        mock_repository.get_by_name.return_value = sample_account

        result = service.get_account_by_name(name, user_id)

        assert result == sample_account
        mock_repository.get_by_name.assert_called_once_with(name, user_id)

    def test_get_account_by_name_not_found(self, service, mock_repository, user_id):
        name = "Nonexistent Account"
        mock_repository.get_by_name.return_value = None

        result = service.get_account_by_name(name, user_id)

        assert result is None
        mock_repository.get_by_name.assert_called_once_with(name, user_id)

    def test_get_all_accounts(self, service, mock_repository, user_id):
        accounts = [
            Account(id=uuid4(), name="Account 1", user_id=user_id),
            Account(id=uuid4(), name="Account 2", user_id=user_id),
        ]
        mock_repository.get_all.return_value = accounts

        result = service.get_all_accounts(user_id)

        assert result == accounts
        mock_repository.get_all.assert_called_once_with(user_id)

    def test_update_account(self, service, mock_repository, sample_account, user_id):
        account_id = sample_account.id
        mock_repository.get_by_id.return_value = sample_account
        mock_repository.update.return_value = sample_account

        new_name = "Updated Account"

        result = service.update_account(
            account_id=account_id,
            name=new_name,
            user_id=user_id,
        )

        assert result == sample_account
        mock_repository.get_by_id.assert_called_once_with(account_id, user_id)
        mock_repository.update.assert_called_once_with(sample_account)
        assert sample_account.name == new_name

    def test_update_account_not_found(self, service, mock_repository, user_id):
        account_id = uuid4()
        mock_repository.get_by_id.return_value = None

        result = service.update_account(
            account_id=account_id,
            name="Updated Account",
            user_id=user_id,
        )

        assert result is None
        mock_repository.get_by_id.assert_called_once_with(account_id, user_id)
        mock_repository.update.assert_not_called()

    def test_delete_account(self, service, mock_repository, sample_account, user_id):
        account_id = sample_account.id
        mock_repository.get_by_id.return_value = sample_account

        result = service.delete_account(account_id, user_id)

        assert result is True
        mock_repository.get_by_id.assert_called_once_with(account_id, user_id)
        mock_repository.delete.assert_called_once_with(account_id, user_id)

    def test_delete_account_not_found(self, service, mock_repository, user_id):
        account_id = uuid4()
        mock_repository.get_by_id.return_value = None

        result = service.delete_account(account_id, user_id)

        assert result is False
        mock_repository.get_by_id.assert_called_once_with(account_id, user_id)
        mock_repository.delete.assert_not_called()

    def test_upsert_accounts_from_csv_new_accounts(self, service, mock_repository, user_id):
        csv_content = "name\nAccount 1\nAccount 2"
        mock_repository.get_by_name.return_value = None
        created_accounts = [
            Account(id=uuid4(), name="Account 1", user_id=user_id),
            Account(id=uuid4(), name="Account 2", user_id=user_id),
        ]
        mock_repository.create.side_effect = created_accounts

        result = service.upsert_accounts_from_csv(csv_content, user_id)

        assert len(result) == 2
        assert result == created_accounts
        assert mock_repository.get_by_name.call_count == 2
        assert mock_repository.create.call_count == 2

    def test_upsert_accounts_from_csv_existing_accounts(self, service, mock_repository, user_id):
        csv_content = "name\nAccount 1"
        existing_account = Account(id=uuid4(), name="Account 1", user_id=user_id)
        mock_repository.get_by_name.return_value = existing_account

        result = service.upsert_accounts_from_csv(csv_content, user_id)

        assert len(result) == 1
        assert result[0] == existing_account
        mock_repository.get_by_name.assert_called_once_with("Account 1", user_id)
        mock_repository.create.assert_not_called()

    def test_upsert_accounts_from_csv_mixed(self, service, mock_repository, user_id):
        csv_content = "name\nExisting Account\nNew Account"
        existing_account = Account(id=uuid4(), name="Existing Account", user_id=user_id)
        new_account = Account(id=uuid4(), name="New Account", user_id=user_id)

        def mock_get_by_name(name, uid):
            return existing_account if name == "Existing Account" else None

        mock_repository.get_by_name.side_effect = mock_get_by_name
        mock_repository.create.return_value = new_account

        result = service.upsert_accounts_from_csv(csv_content, user_id)

        assert len(result) == 2
        assert existing_account in result
        assert new_account in result
        assert mock_repository.get_by_name.call_count == 2
        mock_repository.create.assert_called_once()

    def test_upsert_accounts_from_csv_missing_name_column(self, service, mock_repository, user_id):
        csv_content = "invalid_column\nValue 1"

        with pytest.raises(
            ValidationError,
            match="CSV must contain 'name' column",
        ):
            service.upsert_accounts_from_csv(csv_content, user_id)

    def test_upsert_accounts_from_csv_empty_names_skipped(self, service, mock_repository, user_id):
        csv_content = "name\nValid Account\n\n   \nAnother Account"
        created_accounts = [
            Account(id=uuid4(), name="Valid Account", user_id=user_id),
            Account(id=uuid4(), name="Another Account", user_id=user_id),
        ]
        mock_repository.get_by_name.return_value = None
        mock_repository.create.side_effect = created_accounts

        result = service.upsert_accounts_from_csv(csv_content, user_id)

        assert len(result) == 2
        assert mock_repository.get_by_name.call_count == 2
        assert mock_repository.create.call_count == 2
