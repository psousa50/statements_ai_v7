import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.domain.models.transaction import Transaction
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService


class TestTransactionService:
    """Unit tests for TransactionService"""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing"""
        repository = MagicMock(spec=TransactionRepository)
        return repository

    @pytest.fixture
    def service(self, mock_repository):
        """Create a service with the mock repository"""
        return TransactionService(mock_repository)

    @pytest.fixture
    def sample_transaction(self):
        """Create a sample transaction for testing"""
        transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Test Transaction",
            amount=Decimal("100.50"),
        )
        return transaction

    def test_create_transaction(self, service, mock_repository, sample_transaction):
        """Test creating a transaction"""
        # Arrange
        mock_repository.create.return_value = sample_transaction
        transaction_date = date(2023, 4, 15)
        description = "Test Transaction"
        amount = Decimal("100.50")

        # Act
        result = service.create_transaction(
            transaction_date=transaction_date,
            description=description,
            amount=amount,
        )

        # Assert
        assert result == sample_transaction
        mock_repository.create.assert_called_once()
        # Check that the transaction passed to create has the correct attributes
        created_transaction = mock_repository.create.call_args[0][0]
        assert created_transaction.date == transaction_date
        assert created_transaction.description == description
        assert created_transaction.amount == amount

    def test_get_transaction(self, service, mock_repository, sample_transaction):
        """Test getting a transaction by ID"""
        # Arrange
        transaction_id = sample_transaction.id
        mock_repository.get_by_id.return_value = sample_transaction

        # Act
        result = service.get_transaction(transaction_id)

        # Assert
        assert result == sample_transaction
        mock_repository.get_by_id.assert_called_once_with(transaction_id)

    def test_get_transaction_not_found(self, service, mock_repository):
        """Test getting a transaction that doesn't exist"""
        # Arrange
        transaction_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.get_transaction(transaction_id)

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(transaction_id)

    def test_get_all_transactions(self, service, mock_repository):
        """Test getting all transactions"""
        # Arrange
        transactions = [
            Transaction(
                id=uuid4(),
                date=date(2023, 4, 15),
                description="Transaction 1",
                amount=Decimal("100.50"),
            ),
            Transaction(
                id=uuid4(),
                date=date(2023, 4, 16),
                description="Transaction 2",
                amount=Decimal("200.75"),
            ),
        ]
        mock_repository.get_all.return_value = transactions

        # Act
        result = service.get_all_transactions()

        # Assert
        assert result == transactions
        mock_repository.get_all.assert_called_once()

    def test_update_transaction(self, service, mock_repository, sample_transaction):
        """Test updating a transaction"""
        # Arrange
        transaction_id = sample_transaction.id
        mock_repository.get_by_id.return_value = sample_transaction
        mock_repository.update.return_value = sample_transaction

        new_date = date(2023, 4, 20)
        new_description = "Updated Transaction"
        new_amount = Decimal("150.75")

        # Act
        result = service.update_transaction(
            transaction_id=transaction_id,
            transaction_date=new_date,
            description=new_description,
            amount=new_amount,
        )

        # Assert
        assert result == sample_transaction
        mock_repository.get_by_id.assert_called_once_with(transaction_id)
        mock_repository.update.assert_called_once_with(sample_transaction)
        
        # Check that the transaction was updated with the new values
        assert sample_transaction.date == new_date
        assert sample_transaction.description == new_description
        assert sample_transaction.amount == new_amount

    def test_update_transaction_not_found(self, service, mock_repository):
        """Test updating a transaction that doesn't exist"""
        # Arrange
        transaction_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.update_transaction(
            transaction_id=transaction_id,
            transaction_date=date(2023, 4, 20),
            description="Updated Transaction",
            amount=Decimal("150.75"),
        )

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(transaction_id)
        mock_repository.update.assert_not_called()

    def test_delete_transaction(self, service, mock_repository):
        """Test deleting a transaction"""
        # Arrange
        transaction_id = uuid4()
        mock_repository.delete.return_value = True

        # Act
        result = service.delete_transaction(transaction_id)

        # Assert
        assert result is True
        mock_repository.delete.assert_called_once_with(transaction_id)

    def test_delete_transaction_not_found(self, service, mock_repository):
        """Test deleting a transaction that doesn't exist"""
        # Arrange
        transaction_id = uuid4()
        mock_repository.delete.return_value = False

        # Act
        result = service.delete_transaction(transaction_id)

        # Assert
        assert result is False
        mock_repository.delete.assert_called_once_with(transaction_id)
