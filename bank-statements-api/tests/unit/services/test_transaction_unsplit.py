from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService, TransactionSplitConflictError
from app.services.transaction_enhancement import TransactionEnhancer


def _make_transaction(**overrides):
    defaults = dict(
        id=uuid4(),
        date=date(2024, 3, 10),
        description="Supermarket Shop",
        normalized_description="supermarket shop",
        amount=Decimal("100.00"),
        categorization_status=CategorizationStatus.UNCATEGORIZED,
        sort_index=0,
        source_type=SourceType.UPLOAD,
        exclude_from_analytics=False,
        row_index=0,
        statement_id=uuid4(),
        account_id=uuid4(),
        user_id=uuid4(),
    )
    defaults.update(overrides)
    return Transaction(**defaults)


class TestUnsplitTransaction:
    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_repository(self):
        return MagicMock(spec=TransactionRepository)

    @pytest.fixture
    def service(self, mock_repository):
        return TransactionService(
            mock_repository,
            MagicMock(spec=InitialBalanceRepository),
            MagicMock(spec=EnhancementRuleRepository),
            MagicMock(spec=TransactionEnhancer),
        )

    def test_unsplit_returns_none_when_transaction_not_found(self, service, mock_repository, user_id):
        mock_repository.get_by_id.return_value = None

        result = service.unsplit_transaction(transaction_id=uuid4(), user_id=user_id)

        assert result is None

    def test_unsplit_raises_conflict_when_not_a_split_parent(self, service, mock_repository, user_id):
        parent = _make_transaction(user_id=user_id)
        mock_repository.get_by_id.return_value = parent
        mock_repository.has_split_children.return_value = False

        with pytest.raises(TransactionSplitConflictError):
            service.unsplit_transaction(transaction_id=parent.id, user_id=user_id)

    def test_unsplit_deletes_split_children(self, service, mock_repository, user_id):
        parent = _make_transaction(user_id=user_id, exclude_from_analytics=True)
        mock_repository.get_by_id.return_value = parent
        mock_repository.has_split_children.return_value = True
        mock_repository.unsplit_transaction.return_value = parent

        service.unsplit_transaction(transaction_id=parent.id, user_id=user_id)

        mock_repository.unsplit_transaction.assert_called_once()

    def test_unsplit_restores_exclude_from_analytics_to_false(self, service, mock_repository, user_id):
        parent = _make_transaction(user_id=user_id, exclude_from_analytics=True)
        mock_repository.get_by_id.return_value = parent
        mock_repository.has_split_children.return_value = True
        mock_repository.unsplit_transaction.return_value = parent

        service.unsplit_transaction(transaction_id=parent.id, user_id=user_id)

        call_args = mock_repository.unsplit_transaction.call_args
        passed_parent = call_args[0][0]
        assert passed_parent.exclude_from_analytics is False

    def test_unsplit_returns_updated_parent(self, service, mock_repository, user_id):
        parent = _make_transaction(user_id=user_id, exclude_from_analytics=True)
        mock_repository.get_by_id.return_value = parent
        mock_repository.has_split_children.return_value = True
        mock_repository.unsplit_transaction.return_value = parent

        result = service.unsplit_transaction(transaction_id=parent.id, user_id=user_id)

        assert result is parent

    def test_unsplit_calls_repository_with_correct_parent(self, service, mock_repository, user_id):
        parent = _make_transaction(user_id=user_id, exclude_from_analytics=True)
        mock_repository.get_by_id.return_value = parent
        mock_repository.has_split_children.return_value = True
        mock_repository.unsplit_transaction.return_value = parent

        service.unsplit_transaction(transaction_id=parent.id, user_id=user_id)

        call_args = mock_repository.unsplit_transaction.call_args
        passed_parent = call_args[0][0]
        assert passed_parent.id == parent.id

    def test_unsplit_returns_parent_with_is_split_parent_false(self, service, mock_repository, user_id):
        parent = _make_transaction(user_id=user_id, exclude_from_analytics=True)
        mock_repository.get_by_id.return_value = parent
        mock_repository.has_split_children.return_value = True
        returned_parent = _make_transaction(user_id=user_id, exclude_from_analytics=False)
        returned_parent.is_split_parent = False
        mock_repository.unsplit_transaction.return_value = returned_parent

        result = service.unsplit_transaction(transaction_id=parent.id, user_id=user_id)

        assert result.is_split_parent is False
