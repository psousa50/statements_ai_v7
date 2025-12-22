from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from app.domain.models.refresh_token import RefreshToken  # noqa: F401 - Required for SQLAlchemy mapper
from app.domain.models.transaction import Transaction
from app.domain.models.user import User
from app.ports.repositories.transaction import TransactionRepository

load_dotenv(".env.test")


@pytest.fixture
def test_user_id():
    return uuid4()


@pytest.fixture
def test_user(test_user_id):
    return User(
        id=test_user_id,
        email="test@example.com",
        name="Test User",
        oauth_provider="google",
        oauth_id="test-oauth-id",
    )


@pytest.fixture
def sample_transaction_data():
    return {
        "id": uuid4(),
        "date": date(2023, 4, 15),
        "description": "Test Transaction",
        "amount": Decimal("100.50"),
    }


@pytest.fixture
def sample_transaction(sample_transaction_data):
    return Transaction(**sample_transaction_data)


@pytest.fixture
def mock_transaction_repository():
    return MagicMock(spec=TransactionRepository)
