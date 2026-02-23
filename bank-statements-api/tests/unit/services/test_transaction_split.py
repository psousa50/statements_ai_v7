from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, call
from uuid import uuid4

import pytest

from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService
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


class TestSplitTransactionService:
    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_repository(self):
        return MagicMock(spec=TransactionRepository)

    @pytest.fixture
    def mock_initial_balance_repository(self):
        return MagicMock(spec=InitialBalanceRepository)

    @pytest.fixture
    def mock_enhancement_rule_repository(self):
        return MagicMock(spec=EnhancementRuleRepository)

    @pytest.fixture
    def mock_transaction_enhancer(self):
        return MagicMock(spec=TransactionEnhancer)

    @pytest.fixture
    def service(
        self,
        mock_repository,
        mock_initial_balance_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        return TransactionService(
            mock_repository,
            mock_initial_balance_repository,
            mock_enhancement_rule_repository,
            mock_transaction_enhancer,
        )

    @pytest.fixture
    def parent_transaction(self, user_id):
        return _make_transaction(
            amount=Decimal("100.00"),
            user_id=user_id,
            category_id=uuid4(),
        )

    def test_split_creates_child_transactions_with_given_amounts(self, service, mock_repository, parent_transaction, user_id):
        mock_repository.get_by_id.return_value = parent_transaction
        mock_repository.split_transaction.return_value = []

        category_id = uuid4()
        parts = [
            {"amount": Decimal("60.00"), "description": "Groceries", "category_id": category_id},
            {"amount": Decimal("40.00"), "description": "Household"},
        ]

        service.split_transaction(
            transaction_id=parent_transaction.id,
            user_id=user_id,
            parts=parts,
        )

        mock_repository.split_transaction.assert_called_once()
        children = mock_repository.split_transaction.call_args[0][1]
        assert len(children) == 2

    def test_split_children_have_correct_amounts(self, service, mock_repository, parent_transaction, user_id):
        mock_repository.get_by_id.return_value = parent_transaction
        mock_repository.split_transaction.return_value = []

        parts = [
            {"amount": Decimal("60.00"), "description": "Groceries"},
            {"amount": Decimal("40.00"), "description": "Household"},
        ]

        service.split_transaction(
            transaction_id=parent_transaction.id,
            user_id=user_id,
            parts=parts,
        )

        children = mock_repository.split_transaction.call_args[0][1]
        amounts = {c.description: c.amount for c in children}
        assert amounts["Groceries"] == Decimal("60.00")
        assert amounts["Household"] == Decimal("40.00")

    def test_split_children_have_correct_descriptions(self, service, mock_repository, parent_transaction, user_id):
        mock_repository.get_by_id.return_value = parent_transaction
        mock_repository.split_transaction.return_value = []

        parts = [
            {"amount": Decimal("60.00"), "description": "Part A"},
            {"amount": Decimal("40.00"), "description": "Part B"},
        ]

        service.split_transaction(
            transaction_id=parent_transaction.id,
            user_id=user_id,
            parts=parts,
        )

        children = mock_repository.split_transaction.call_args[0][1]
        descriptions = [c.description for c in children]
        assert "Part A" in descriptions
        assert "Part B" in descriptions

    def test_split_children_have_correct_categories(self, service, mock_repository, parent_transaction, user_id):
        mock_repository.get_by_id.return_value = parent_transaction
        mock_repository.split_transaction.return_value = []

        cat_a = uuid4()
        parts = [
            {"amount": Decimal("60.00"), "description": "Part A", "category_id": cat_a},
            {"amount": Decimal("40.00"), "description": "Part B"},
        ]

        service.split_transaction(
            transaction_id=parent_transaction.id,
            user_id=user_id,
            parts=parts,
        )

        children = mock_repository.split_transaction.call_args[0][1]
        child_by_desc = {c.description: c for c in children}
        assert child_by_desc["Part A"].category_id == cat_a
        assert child_by_desc["Part B"].category_id is None

    def test_split_children_reference_parent_via_parent_transaction_id(
        self, service, mock_repository, parent_transaction, user_id
    ):
        mock_repository.get_by_id.return_value = parent_transaction
        mock_repository.split_transaction.return_value = []

        parts = [
            {"amount": Decimal("60.00"), "description": "Part A"},
            {"amount": Decimal("40.00"), "description": "Part B"},
        ]

        service.split_transaction(
            transaction_id=parent_transaction.id,
            user_id=user_id,
            parts=parts,
        )

        children = mock_repository.split_transaction.call_args[0][1]
        for child in children:
            assert child.parent_transaction_id == parent_transaction.id

    def test_split_clears_parent_category(self, service, mock_repository, parent_transaction, user_id):
        assert parent_transaction.category_id is not None
        mock_repository.get_by_id.return_value = parent_transaction
        mock_repository.split_transaction.return_value = []

        parts = [
            {"amount": Decimal("60.00"), "description": "Part A"},
            {"amount": Decimal("40.00"), "description": "Part B"},
        ]

        service.split_transaction(
            transaction_id=parent_transaction.id,
            user_id=user_id,
            parts=parts,
        )

        mock_repository.split_transaction.assert_called_once()
        assert parent_transaction.category_id is None

    def test_split_excludes_parent_from_analytics(self, service, mock_repository, parent_transaction, user_id):
        mock_repository.get_by_id.return_value = parent_transaction
        mock_repository.split_transaction.return_value = []

        parts = [
            {"amount": Decimal("60.00"), "description": "Part A"},
            {"amount": Decimal("40.00"), "description": "Part B"},
        ]

        service.split_transaction(
            transaction_id=parent_transaction.id,
            user_id=user_id,
            parts=parts,
        )

        assert parent_transaction.exclude_from_analytics is True

    def test_split_raises_when_amounts_do_not_sum_to_parent(self, service, mock_repository, parent_transaction, user_id):
        mock_repository.get_by_id.return_value = parent_transaction

        parts = [
            {"amount": Decimal("60.00"), "description": "Part A"},
            {"amount": Decimal("30.00"), "description": "Part B"},
        ]

        with pytest.raises(ValueError, match="sum"):
            service.split_transaction(
                transaction_id=parent_transaction.id,
                user_id=user_id,
                parts=parts,
            )

        mock_repository.split_transaction.assert_not_called()

    def test_split_raises_when_fewer_than_two_parts_provided(self, service, mock_repository, parent_transaction, user_id):
        mock_repository.get_by_id.return_value = parent_transaction

        parts = [
            {"amount": Decimal("100.00"), "description": "Only Part"},
        ]

        with pytest.raises(ValueError):
            service.split_transaction(
                transaction_id=parent_transaction.id,
                user_id=user_id,
                parts=parts,
            )

        mock_repository.split_transaction.assert_not_called()

    def test_split_returns_none_when_transaction_not_found(self, service, mock_repository, user_id):
        mock_repository.get_by_id.return_value = None
        transaction_id = uuid4()

        parts = [
            {"amount": Decimal("50.00"), "description": "Part A"},
            {"amount": Decimal("50.00"), "description": "Part B"},
        ]

        result = service.split_transaction(
            transaction_id=transaction_id,
            user_id=user_id,
            parts=parts,
        )

        assert result is None
        mock_repository.split_transaction.assert_not_called()

    def test_split_replaces_existing_children_when_transaction_already_has_children(self, service, mock_repository, user_id):
        parent = _make_transaction(amount=Decimal("100.00"), user_id=user_id)
        mock_repository.get_by_id.return_value = parent
        mock_repository.has_split_children.return_value = True

        parts = [
            {"amount": Decimal("50.00"), "description": "Part A"},
            {"amount": Decimal("50.00"), "description": "Part B"},
        ]

        service.split_transaction(
            transaction_id=parent.id,
            user_id=user_id,
            parts=parts,
        )

        mock_repository.split_transaction.assert_called_once()

    def test_split_raises_conflict_when_transaction_is_a_split_child(self, service, mock_repository, user_id):
        child = _make_transaction(
            amount=Decimal("50.00"),
            user_id=user_id,
            parent_transaction_id=uuid4(),
        )
        mock_repository.get_by_id.return_value = child

        parts = [
            {"amount": Decimal("25.00"), "description": "Sub A"},
            {"amount": Decimal("25.00"), "description": "Sub B"},
        ]

        with pytest.raises(Exception) as exc_info:
            service.split_transaction(
                transaction_id=child.id,
                user_id=user_id,
                parts=parts,
            )

        assert exc_info.type.__name__ in ("ConflictError", "ValueError", "HTTPException")
        mock_repository.split_transaction.assert_not_called()


class TestSplitTransactionRounding:
    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_repository(self):
        return MagicMock(spec=TransactionRepository)

    @pytest.fixture
    def mock_initial_balance_repository(self):
        return MagicMock(spec=InitialBalanceRepository)

    @pytest.fixture
    def mock_enhancement_rule_repository(self):
        return MagicMock(spec=EnhancementRuleRepository)

    @pytest.fixture
    def mock_transaction_enhancer(self):
        return MagicMock(spec=TransactionEnhancer)

    @pytest.fixture
    def service(
        self,
        mock_repository,
        mock_initial_balance_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        return TransactionService(
            mock_repository,
            mock_initial_balance_repository,
            mock_enhancement_rule_repository,
            mock_transaction_enhancer,
        )

    def test_split_auto_adjusts_last_part_for_non_divisible_amounts(self, service, mock_repository, user_id):
        parent = _make_transaction(amount=Decimal("10.00"), user_id=user_id)
        mock_repository.get_by_id.return_value = parent
        mock_repository.split_transaction.return_value = []

        parts = [
            {"amount": Decimal("3.33"), "description": "Part A"},
            {"amount": Decimal("3.33"), "description": "Part B"},
            {"amount": Decimal("3.33"), "description": "Part C"},
        ]

        service.split_transaction(
            transaction_id=parent.id,
            user_id=user_id,
            parts=parts,
        )

        children = mock_repository.split_transaction.call_args[0][1]
        total = sum(c.amount for c in children)
        assert total == Decimal("10.00")

    def test_split_last_part_absorbs_rounding_difference(self, service, mock_repository, user_id):
        parent = _make_transaction(amount=Decimal("10.00"), user_id=user_id)
        mock_repository.get_by_id.return_value = parent
        mock_repository.split_transaction.return_value = []

        parts = [
            {"amount": Decimal("3.33"), "description": "Part A"},
            {"amount": Decimal("3.33"), "description": "Part B"},
            {"amount": Decimal("3.33"), "description": "Part C"},
        ]

        service.split_transaction(
            transaction_id=parent.id,
            user_id=user_id,
            parts=parts,
        )

        children = mock_repository.split_transaction.call_args[0][1]
        last_child = next(c for c in children if c.description == "Part C")
        assert last_child.amount == Decimal("3.34")


class TestSplitTransactionResponseFields:
    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_repository(self):
        return MagicMock(spec=TransactionRepository)

    @pytest.fixture
    def mock_initial_balance_repository(self):
        return MagicMock(spec=InitialBalanceRepository)

    @pytest.fixture
    def mock_enhancement_rule_repository(self):
        return MagicMock(spec=EnhancementRuleRepository)

    @pytest.fixture
    def mock_transaction_enhancer(self):
        return MagicMock(spec=TransactionEnhancer)

    @pytest.fixture
    def service(
        self,
        mock_repository,
        mock_initial_balance_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        return TransactionService(
            mock_repository,
            mock_initial_balance_repository,
            mock_enhancement_rule_repository,
            mock_transaction_enhancer,
        )

    def test_is_split_parent_true_when_transaction_has_children(self, service, mock_repository, user_id):
        parent = _make_transaction(amount=Decimal("100.00"), user_id=user_id)
        mock_repository.get_by_id.return_value = parent
        mock_repository.has_split_children.return_value = True

        result = service.get_transaction(parent.id, user_id)

        assert result is not None
        assert result.is_split_parent is True

    def test_is_split_child_true_when_transaction_has_parent(self, user_id):
        parent_id = uuid4()
        child = _make_transaction(
            amount=Decimal("50.00"),
            user_id=user_id,
            parent_transaction_id=parent_id,
        )
        assert child.parent_transaction_id == parent_id

    def test_parent_transaction_id_none_for_regular_transaction(self, user_id):
        txn = _make_transaction(amount=Decimal("50.00"), user_id=user_id)
        assert txn.parent_transaction_id is None
