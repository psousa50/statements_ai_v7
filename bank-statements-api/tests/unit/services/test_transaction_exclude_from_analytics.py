from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.models.transaction import Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService
from app.services.transaction_enhancement import TransactionEnhancer


class TestToggleExcludeFromAnalytics:
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
    def included_transaction(self):
        return Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Regular Purchase",
            normalized_description="regular purchase",
            amount=Decimal("50.00"),
            exclude_from_analytics=False,
        )

    @pytest.fixture
    def excluded_transaction(self):
        return Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="One-off Property Purchase",
            normalized_description="one-off property purchase",
            amount=Decimal("250000.00"),
            exclude_from_analytics=True,
        )

    def test_exclude_transaction_from_analytics(self, service, mock_repository, included_transaction, user_id):
        mock_repository.get_by_id.return_value = included_transaction
        mock_repository.update.return_value = included_transaction

        result = service.toggle_exclude_from_analytics(
            transaction_id=included_transaction.id,
            user_id=user_id,
            exclude_from_analytics=True,
        )

        assert result.exclude_from_analytics is True
        mock_repository.get_by_id.assert_called_once_with(included_transaction.id, user_id)
        mock_repository.update.assert_called_once_with(included_transaction)

    def test_include_previously_excluded_transaction(self, service, mock_repository, excluded_transaction, user_id):
        mock_repository.get_by_id.return_value = excluded_transaction
        mock_repository.update.return_value = excluded_transaction

        result = service.toggle_exclude_from_analytics(
            transaction_id=excluded_transaction.id,
            user_id=user_id,
            exclude_from_analytics=False,
        )

        assert result.exclude_from_analytics is False
        mock_repository.get_by_id.assert_called_once_with(excluded_transaction.id, user_id)
        mock_repository.update.assert_called_once_with(excluded_transaction)

    def test_toggle_exclude_transaction_not_found(self, service, mock_repository, user_id):
        transaction_id = uuid4()
        mock_repository.get_by_id.return_value = None

        result = service.toggle_exclude_from_analytics(
            transaction_id=transaction_id,
            user_id=user_id,
            exclude_from_analytics=True,
        )

        assert result is None
        mock_repository.get_by_id.assert_called_once_with(transaction_id, user_id)
        mock_repository.update.assert_not_called()

    def test_exclude_does_not_change_other_fields(self, service, mock_repository, included_transaction, user_id):
        original_description = included_transaction.description
        original_amount = included_transaction.amount
        original_category_id = included_transaction.category_id
        original_date = included_transaction.date

        mock_repository.get_by_id.return_value = included_transaction
        mock_repository.update.return_value = included_transaction

        service.toggle_exclude_from_analytics(
            transaction_id=included_transaction.id,
            user_id=user_id,
            exclude_from_analytics=True,
        )

        assert included_transaction.description == original_description
        assert included_transaction.amount == original_amount
        assert included_transaction.category_id == original_category_id
        assert included_transaction.date == original_date


class TestNewTransactionsDefaultIncluded:
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
        repository = MagicMock(spec=EnhancementRuleRepository)
        repository.find_matching_rules_batch.return_value = []
        repository.find_by_normalized_description.return_value = None
        return repository

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

    def test_new_transaction_defaults_to_not_excluded(self):
        transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="New Transaction",
            normalized_description="new transaction",
            amount=Decimal("100.50"),
        )

        assert transaction.exclude_from_analytics is False

    def test_saved_transactions_from_dtos_default_to_not_excluded(self, service, mock_repository, user_id):
        from app.domain.dto.statement_processing import TransactionDTO

        account_id = uuid4()
        dtos = [
            TransactionDTO(
                date="2025-01-15",
                amount=Decimal("-100.00"),
                description="Uploaded Transaction",
                user_id=user_id,
                account_id=str(account_id),
                statement_id=str(uuid4()),
                row_index=0,
                sort_index=0,
                source_type="UPLOAD",
            ),
        ]

        mock_repository.count_by_date_and_amount.return_value = 0
        mock_repository.create_many.return_value = []

        service.save_transactions_from_dtos(dtos)

        saved_transactions = mock_repository.create_many.call_args[0][0]
        assert saved_transactions[0].exclude_from_analytics is False


class TestCategoryTotalsExcludesAnalyticsExcluded:
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

    def test_get_category_totals_passes_exclude_from_analytics(self, service, mock_repository, user_id):
        category_id = uuid4()
        mock_repository.get_category_totals.return_value = {
            category_id: {
                "total_amount": Decimal("100.00"),
                "transaction_count": Decimal("2"),
            }
        }

        service.get_category_totals(user_id=user_id)

        call_kwargs = mock_repository.get_category_totals.call_args[1]
        assert call_kwargs.get("exclude_from_analytics") is True

    def test_get_category_time_series_passes_exclude_from_analytics(self, service, mock_repository, user_id):
        mock_repository.get_category_time_series.return_value = []

        service.get_category_time_series(user_id=user_id)

        call_kwargs = mock_repository.get_category_time_series.call_args[1]
        assert call_kwargs.get("exclude_from_analytics") is True


class TestTransactionListExcludeFromAnalyticsFilter:
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

    def test_get_transactions_paginated_with_exclude_from_analytics_filter(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(
            user_id=user_id,
            exclude_from_analytics=True,
        )

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert call_kwargs.get("exclude_from_analytics") is True

    def test_get_transactions_paginated_without_exclude_filter(self, service, mock_repository, user_id):
        mock_repository.get_paginated.return_value = ([], 0, Decimal("0"))

        service.get_transactions_paginated(user_id=user_id)

        call_kwargs = mock_repository.get_paginated.call_args[1]
        assert "exclude_from_analytics" not in call_kwargs or call_kwargs.get("exclude_from_analytics") is None
