from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.models.transaction import Transaction
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService


class TestTransactionService:
    @pytest.fixture
    def mock_repository(self):
        repository = MagicMock(spec=TransactionRepository)
        return repository

    @pytest.fixture
    def service(self, mock_repository):
        return TransactionService(mock_repository)

    @pytest.fixture
    def sample_transaction(self):
        transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Test Transaction",
            normalized_description="test transaction",
            amount=Decimal("100.50"),
        )
        return transaction

    def test_create_transaction(self, service, mock_repository, sample_transaction):
        mock_repository.create.return_value = sample_transaction
        transaction_date = date(2023, 4, 15)
        description = "Test Transaction"
        amount = Decimal("100.50")
        source_id = uuid4()

        result = service.create_transaction(
            transaction_date=transaction_date,
            description=description,
            amount=amount,
            source_id=source_id,
        )

        assert result == sample_transaction
        mock_repository.create.assert_called_once()
        created_transaction = mock_repository.create.call_args[0][0]
        assert created_transaction.date == transaction_date
        assert created_transaction.description == description
        assert created_transaction.amount == amount
        assert created_transaction.source_id == source_id

    def test_get_transaction(self, service, mock_repository, sample_transaction):
        transaction_id = sample_transaction.id
        mock_repository.get_by_id.return_value = sample_transaction

        result = service.get_transaction(transaction_id)
        assert result == sample_transaction
        mock_repository.get_by_id.assert_called_once_with(transaction_id)

    def test_get_transaction_not_found(self, service, mock_repository):
        transaction_id = uuid4()
        mock_repository.get_by_id.return_value = None

        result = service.get_transaction(transaction_id)

        assert result is None
        mock_repository.get_by_id.assert_called_once_with(transaction_id)

    def test_get_all_transactions(self, service, mock_repository):
        transactions = [
            Transaction(
                id=uuid4(),
                date=date(2023, 4, 15),
                description="Transaction 1",
                normalized_description="transaction",
                amount=Decimal("100.50"),
            ),
            Transaction(
                id=uuid4(),
                date=date(2023, 4, 16),
                description="Transaction 2",
                normalized_description="transaction",
                amount=Decimal("200.75"),
            ),
        ]
        mock_repository.get_all.return_value = transactions

        result = service.get_all_transactions()

        assert result == transactions
        mock_repository.get_all.assert_called_once()

    def test_update_transaction(self, service, mock_repository, sample_transaction):
        transaction_id = sample_transaction.id
        mock_repository.get_by_id.return_value = sample_transaction
        mock_repository.update.return_value = sample_transaction

        new_date = date(2023, 4, 20)
        new_description = "Updated Transaction"
        new_amount = Decimal("150.75")
        new_source_id = uuid4()

        result = service.update_transaction(
            transaction_id=transaction_id,
            transaction_date=new_date,
            description=new_description,
            amount=new_amount,
            source_id=new_source_id,
        )

        assert result == sample_transaction
        mock_repository.get_by_id.assert_called_once_with(transaction_id)
        mock_repository.update.assert_called_once_with(sample_transaction)
        assert sample_transaction.date == new_date
        assert sample_transaction.description == new_description
        assert sample_transaction.amount == new_amount
        assert sample_transaction.source_id == new_source_id

    def test_update_transaction_not_found(self, service, mock_repository):
        transaction_id = uuid4()
        mock_repository.get_by_id.return_value = None
        result = service.update_transaction(
            transaction_id=transaction_id,
            transaction_date=date(2023, 4, 20),
            description="Updated Transaction",
            amount=Decimal("150.75"),
            source_id=uuid4(),
        )

        assert result is None
        mock_repository.get_by_id.assert_called_once_with(transaction_id)
        mock_repository.update.assert_not_called()

    def test_delete_transaction(self, service, mock_repository):
        transaction_id = uuid4()
        mock_repository.delete.return_value = True
        result = service.delete_transaction(transaction_id)

        assert result is True
        mock_repository.delete.assert_called_once_with(transaction_id)

    def test_delete_transaction_not_found(self, service, mock_repository):
        transaction_id = uuid4()
        mock_repository.delete.return_value = False
        result = service.delete_transaction(transaction_id)

        assert result is False
        mock_repository.delete.assert_called_once_with(transaction_id)
