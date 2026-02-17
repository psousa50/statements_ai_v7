from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.api.errors import ConflictError, NotFoundError, ValidationError
from app.domain.models.tag import Tag
from app.domain.models.transaction import Transaction
from app.ports.repositories.tag import TagRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.tag import TagService


class TestTagService:
    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_tag_repository(self):
        return MagicMock(spec=TagRepository)

    @pytest.fixture
    def mock_transaction_repository(self):
        return MagicMock(spec=TransactionRepository)

    @pytest.fixture
    def service(self, mock_tag_repository, mock_transaction_repository):
        return TagService(mock_tag_repository, mock_transaction_repository)

    @pytest.fixture
    def sample_tag(self, user_id):
        return Tag(id=uuid4(), name="holiday", user_id=user_id)

    @pytest.fixture
    def sample_transaction(self, user_id):
        transaction = MagicMock(spec=Transaction)
        transaction.id = uuid4()
        transaction.user_id = user_id
        transaction.tags = []
        return transaction

    def test_create_tag(self, service, mock_tag_repository, user_id):
        mock_tag_repository.get_by_name_ci.return_value = None
        expected_tag = Tag(id=uuid4(), name="holiday", user_id=user_id)
        mock_tag_repository.create.return_value = expected_tag

        result = service.create_tag(name="holiday", user_id=user_id)

        assert result == expected_tag
        mock_tag_repository.get_by_name_ci.assert_called_once_with("holiday", user_id)
        mock_tag_repository.create.assert_called_once()

    def test_create_tag_strips_whitespace(self, service, mock_tag_repository, user_id):
        mock_tag_repository.get_by_name_ci.return_value = None
        mock_tag_repository.create.return_value = Tag(id=uuid4(), name="holiday", user_id=user_id)

        service.create_tag(name="  holiday  ", user_id=user_id)

        mock_tag_repository.get_by_name_ci.assert_called_once_with("holiday", user_id)
        created_tag = mock_tag_repository.create.call_args[0][0]
        assert created_tag.name == "holiday"

    def test_create_tag_blank_name_raises(self, service, user_id):
        with pytest.raises(ValidationError, match="cannot be blank"):
            service.create_tag(name="   ", user_id=user_id)

    def test_create_tag_too_long_raises(self, service, user_id):
        with pytest.raises(ValidationError, match="cannot exceed 50 characters"):
            service.create_tag(name="a" * 51, user_id=user_id)

    def test_create_tag_duplicate_raises_conflict(self, service, mock_tag_repository, sample_tag, user_id):
        mock_tag_repository.get_by_name_ci.return_value = sample_tag

        with pytest.raises(ConflictError, match="already exists"):
            service.create_tag(name="Holiday", user_id=user_id)

    def test_get_all_tags(self, service, mock_tag_repository, user_id, sample_tag):
        mock_tag_repository.get_all.return_value = [sample_tag]

        result = service.get_all_tags(user_id)

        assert result == [sample_tag]
        mock_tag_repository.get_all.assert_called_once_with(user_id)

    def test_add_tag_to_transaction(
        self,
        service,
        mock_tag_repository,
        mock_transaction_repository,
        sample_tag,
        sample_transaction,
        user_id,
    ):
        mock_tag_repository.get_by_id.return_value = sample_tag
        mock_transaction_repository.get_by_id.return_value = sample_transaction

        service.add_tag_to_transaction(
            transaction_id=sample_transaction.id,
            tag_id=sample_tag.id,
            user_id=user_id,
        )

        mock_tag_repository.add_to_transaction.assert_called_once_with(sample_transaction.id, sample_tag.id)

    def test_add_tag_to_transaction_tag_not_found(self, service, mock_tag_repository, user_id):
        mock_tag_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Tag not found"):
            service.add_tag_to_transaction(transaction_id=uuid4(), tag_id=uuid4(), user_id=user_id)

    def test_add_tag_to_transaction_transaction_not_found(
        self,
        service,
        mock_tag_repository,
        mock_transaction_repository,
        sample_tag,
        user_id,
    ):
        mock_tag_repository.get_by_id.return_value = sample_tag
        mock_transaction_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Transaction not found"):
            service.add_tag_to_transaction(transaction_id=uuid4(), tag_id=sample_tag.id, user_id=user_id)

    def test_add_tag_already_applied_skips(
        self,
        service,
        mock_tag_repository,
        mock_transaction_repository,
        sample_tag,
        sample_transaction,
        user_id,
    ):
        sample_transaction.tags = [sample_tag]
        mock_tag_repository.get_by_id.return_value = sample_tag
        mock_transaction_repository.get_by_id.return_value = sample_transaction

        service.add_tag_to_transaction(
            transaction_id=sample_transaction.id,
            tag_id=sample_tag.id,
            user_id=user_id,
        )

        mock_tag_repository.add_to_transaction.assert_not_called()

    def test_remove_tag_from_transaction(
        self,
        service,
        mock_tag_repository,
        mock_transaction_repository,
        sample_tag,
        sample_transaction,
        user_id,
    ):
        mock_tag_repository.get_by_id.return_value = sample_tag
        mock_transaction_repository.get_by_id.return_value = sample_transaction
        mock_tag_repository.has_transactions.return_value = True

        service.remove_tag_from_transaction(
            transaction_id=sample_transaction.id,
            tag_id=sample_tag.id,
            user_id=user_id,
        )

        mock_tag_repository.remove_from_transaction.assert_called_once_with(sample_transaction.id, sample_tag.id)
        mock_tag_repository.delete.assert_not_called()

    def test_remove_tag_deletes_orphan(
        self,
        service,
        mock_tag_repository,
        mock_transaction_repository,
        sample_tag,
        sample_transaction,
        user_id,
    ):
        mock_tag_repository.get_by_id.return_value = sample_tag
        mock_transaction_repository.get_by_id.return_value = sample_transaction
        mock_tag_repository.has_transactions.return_value = False

        service.remove_tag_from_transaction(
            transaction_id=sample_transaction.id,
            tag_id=sample_tag.id,
            user_id=user_id,
        )

        mock_tag_repository.remove_from_transaction.assert_called_once()
        mock_tag_repository.delete.assert_called_once_with(sample_tag.id, user_id)
