from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.models.account import Account
from app.ports.repositories.account import AccountRepository
from app.services.account import AccountService


class TestAccountService:
    """Unit tests for AccountService"""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing"""
        repository = MagicMock(spec=AccountRepository)
        return repository

    @pytest.fixture
    def service(self, mock_repository):
        """Create a service with the mock repository"""
        return AccountService(mock_repository)

    @pytest.fixture
    def sample_account(self):
        """Create a sample account for testing"""
        account = Account(
            id=uuid4(),
            name="Test Account",
        )
        return account

    def test_create_account(self, service, mock_repository, sample_account):
        """Test creating an account"""
        # Arrange
        mock_repository.create.return_value = sample_account
        name = "Test Account"

        # Act
        result = service.create_account(name=name)

        # Assert
        assert result == sample_account
        mock_repository.create.assert_called_once()
        # Check that the account passed to create has the correct attributes
        created_account = mock_repository.create.call_args[0][0]
        assert created_account.name == name

    def test_get_account_by_id(self, service, mock_repository, sample_account):
        """Test getting an account by ID"""
        # Arrange
        account_id = sample_account.id
        mock_repository.get_by_id.return_value = sample_account

        # Act
        result = service.get_account_by_id(account_id)

        # Assert
        assert result == sample_account
        mock_repository.get_by_id.assert_called_once_with(account_id)

    def test_get_account_by_id_not_found(self, service, mock_repository):
        """Test getting an account that doesn't exist"""
        # Arrange
        account_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.get_account_by_id(account_id)

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(account_id)

    def test_get_account_by_name(self, service, mock_repository, sample_account):
        """Test getting an account by name"""
        # Arrange
        name = sample_account.name
        mock_repository.get_by_name.return_value = sample_account

        # Act
        result = service.get_account_by_name(name)

        # Assert
        assert result == sample_account
        mock_repository.get_by_name.assert_called_once_with(name)

    def test_get_account_by_name_not_found(self, service, mock_repository):
        """Test getting an account by name that doesn't exist"""
        # Arrange
        name = "Nonexistent Account"
        mock_repository.get_by_name.return_value = None

        # Act
        result = service.get_account_by_name(name)

        # Assert
        assert result is None
        mock_repository.get_by_name.assert_called_once_with(name)

    def test_get_all_accounts(self, service, mock_repository):
        """Test getting all accounts"""
        # Arrange
        accounts = [
            Account(id=uuid4(), name="Account 1"),
            Account(id=uuid4(), name="Account 2"),
        ]
        mock_repository.get_all.return_value = accounts

        # Act
        result = service.get_all_accounts()

        # Assert
        assert result == accounts
        mock_repository.get_all.assert_called_once()

    def test_update_account(self, service, mock_repository, sample_account):
        """Test updating an account"""
        # Arrange
        account_id = sample_account.id
        mock_repository.get_by_id.return_value = sample_account
        mock_repository.update.return_value = sample_account

        new_name = "Updated Account"

        # Act
        result = service.update_account(
            account_id=account_id,
            name=new_name,
        )

        # Assert
        assert result == sample_account
        mock_repository.get_by_id.assert_called_once_with(account_id)
        mock_repository.update.assert_called_once_with(sample_account)

        # Check that the account was updated with the new values
        assert sample_account.name == new_name

    def test_update_account_not_found(self, service, mock_repository):
        """Test updating an account that doesn't exist"""
        # Arrange
        account_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.update_account(
            account_id=account_id,
            name="Updated Account",
        )

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(account_id)
        mock_repository.update.assert_not_called()

    def test_delete_account(self, service, mock_repository, sample_account):
        """Test deleting an account"""
        # Arrange
        account_id = sample_account.id
        mock_repository.get_by_id.return_value = sample_account

        # Act
        result = service.delete_account(account_id)

        # Assert
        assert result is True
        mock_repository.get_by_id.assert_called_once_with(account_id)
        mock_repository.delete.assert_called_once_with(account_id)

    def test_delete_account_not_found(self, service, mock_repository):
        """Test deleting an account that doesn't exist"""
        # Arrange
        account_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.delete_account(account_id)

        # Assert
        assert result is False
        mock_repository.get_by_id.assert_called_once_with(account_id)
        mock_repository.delete.assert_not_called()
