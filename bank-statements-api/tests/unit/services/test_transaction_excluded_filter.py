from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService
from app.services.transaction_enhancement import TransactionEnhancer


class TestExcludedTransactionFilter:
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

    def test_filter_passes_exclude_from_analytics_true_to_repository(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(user_id=user_id, exclude_from_analytics=True)

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is True

    def test_filter_passes_exclude_from_analytics_false_to_repository(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(user_id=user_id, exclude_from_analytics=False)

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is False

    def test_filter_passes_none_when_not_specified(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(user_id=user_id)

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is None

    def test_excluded_filter_combined_with_category_filter(self, service, mock_repository, user_id):
        category_id = uuid4()
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
            category_ids=[category_id],
        )

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is True
        assert call_kwargs["category_ids"] == [category_id]

    def test_excluded_filter_combined_with_date_range(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is True
        assert call_kwargs["start_date"] == date(2023, 1, 1)
        assert call_kwargs["end_date"] == date(2023, 12, 31)

    def test_excluded_filter_combined_with_account_and_amount_filters(self, service, mock_repository, user_id):
        account_id = uuid4()
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
            account_id=account_id,
            min_amount=Decimal("50"),
            max_amount=Decimal("200"),
        )

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is True
        assert call_kwargs["account_id"] == account_id
        assert call_kwargs["min_amount"] == Decimal("50")
        assert call_kwargs["max_amount"] == Decimal("200")

    def test_excluded_filter_combined_with_description_search(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
            description_search="rent",
        )

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is True
        assert call_kwargs["description_search"] == "rent"

    def test_excluded_filter_combined_with_tag_filter(self, service, mock_repository, user_id):
        tag_id = uuid4()
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
            tag_ids=[tag_id],
        )

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is True
        assert call_kwargs["tag_ids"] == [tag_id]

    def test_excluded_filter_combined_with_status_filter(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
            status=CategorizationStatus.UNCATEGORIZED,
        )

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs["exclude_from_analytics"] is True
        assert call_kwargs["status"] == CategorizationStatus.UNCATEGORIZED

    def test_response_structure_with_excluded_filter(self, service, mock_repository, user_id):
        excluded_transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Excluded Transaction",
            normalized_description="excluded transaction",
            amount=Decimal("500.00"),
            created_at=datetime.now(timezone.utc),
            categorization_status=CategorizationStatus.UNCATEGORIZED,
            sort_index=0,
            source_type="upload",
            exclude_from_analytics=True,
        )
        mock_repository.get_paginated.return_value = (
            [excluded_transaction],
            1,
            Decimal("500.00"),
        )

        result = service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
        )

        assert result.total == 1
        assert result.transactions[0].exclude_from_analytics is True
        assert result.total_amount == Decimal("500.00")

    def test_empty_result_when_no_excluded_transactions_match(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        result = service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
        )

        assert result.total == 0
        assert result.transactions == []


class TestReincludeUpdatesFilterView:
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

    def test_reinclude_sets_exclude_from_analytics_to_false(self, service, mock_repository, user_id):
        transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Previously Excluded",
            normalized_description="previously excluded",
            amount=Decimal("250.00"),
            exclude_from_analytics=True,
        )
        mock_repository.get_by_id.return_value = transaction
        mock_repository.update.return_value = transaction

        result = service.toggle_exclude_from_analytics(
            transaction_id=transaction.id,
            user_id=user_id,
            exclude_from_analytics=False,
        )

        assert result.exclude_from_analytics is False
        mock_repository.update.assert_called_once_with(transaction)

    def test_reincluded_transaction_no_longer_matches_excluded_filter(self, service, mock_repository, user_id):
        transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Was Excluded",
            normalized_description="was excluded",
            amount=Decimal("100.00"),
            exclude_from_analytics=True,
        )
        mock_repository.get_by_id.return_value = transaction
        mock_repository.update.return_value = transaction

        service.toggle_exclude_from_analytics(
            transaction_id=transaction.id,
            user_id=user_id,
            exclude_from_analytics=False,
        )

        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        result = service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
        )

        assert transaction not in result.transactions
