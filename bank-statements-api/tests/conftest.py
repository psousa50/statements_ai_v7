"""
Common test fixtures for the bank-statements-api tests.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from app.domain.models.transaction import Transaction
from app.ports.repositories.transaction import TransactionRepository

load_dotenv(".env.test")


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for tests"""
    return {
        "id": uuid4(),
        "date": date(2023, 4, 15),
        "description": "Test Transaction",
        "amount": Decimal("100.50"),
    }


@pytest.fixture
def sample_transaction(sample_transaction_data):
    """Sample transaction object for tests"""
    return Transaction(**sample_transaction_data)


@pytest.fixture
def mock_transaction_repository():
    """Mock transaction repository for tests"""
    return MagicMock(spec=TransactionRepository)
