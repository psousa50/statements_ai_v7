"""
Tests for TransactionService using common fixtures from conftest.py
"""
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.transaction import TransactionService


class TestTransactionServiceWithFixtures:
    """Tests for TransactionService using common fixtures"""

    @pytest.fixture
    def service(self, mock_transaction_repository):
        """Create a service with the mock repository from conftest.py"""
        return TransactionService(mock_transaction_repository)

    def test_create_transaction_with_fixtures(self, service, mock_transaction_repository, sample_transaction):
        """Test creating a transaction using fixtures"""
        # Arrange
        mock_transaction_repository.create.return_value = sample_transaction
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
        mock_transaction_repository.create.assert_called_once()
        # Check that the transaction passed to create has the correct attributes
        created_transaction = mock_transaction_repository.create.call_args[0][0]
        assert created_transaction.date == transaction_date
        assert created_transaction.description == description
        assert created_transaction.amount == amount

    def test_get_all_transactions_with_fixtures(self, service, mock_transaction_repository, sample_transaction):
        """Test getting all transactions using fixtures"""
        # Arrange
        mock_transaction_repository.get_all.return_value = [sample_transaction]

        # Act
        result = service.get_all_transactions()

        # Assert
        assert len(result) == 1
        assert result[0] == sample_transaction
        mock_transaction_repository.get_all.assert_called_once()

    def test_update_transaction_with_fixtures(self, service, mock_transaction_repository, sample_transaction):
        """Test updating a transaction using fixtures"""
        # Arrange
        transaction_id = sample_transaction.id
        mock_transaction_repository.get_by_id.return_value = sample_transaction
        mock_transaction_repository.update.return_value = sample_transaction

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
        mock_transaction_repository.get_by_id.assert_called_once_with(transaction_id)
        mock_transaction_repository.update.assert_called_once_with(sample_transaction)
        
        # Check that the transaction was updated with the new values
        assert sample_transaction.date == new_date
        assert sample_transaction.description == new_description
        assert sample_transaction.amount == new_amount
