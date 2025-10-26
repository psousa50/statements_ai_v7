from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.api.schemas import TransactionCreateRequest
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService
from app.services.transaction_enhancement import TransactionEnhancer


class TestTransactionService:
    @pytest.fixture
    def mock_repository(self):
        repository = MagicMock(spec=TransactionRepository)
        return repository

    @pytest.fixture
    def mock_initial_balance_repository(self):
        repository = MagicMock(spec=InitialBalanceRepository)
        return repository

    @pytest.fixture
    def mock_enhancement_rule_repository(self):
        repository = MagicMock(spec=EnhancementRuleRepository)
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

    def test_create_transaction(
        self,
        service,
        mock_repository,
        sample_transaction,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        mock_repository.create_transaction.return_value = sample_transaction
        transaction_date = date(2023, 4, 15)
        description = "Test Transaction"
        amount = Decimal("100.50")
        account_id = uuid4()

        mock_enhancement_rule_repository.get_all.return_value = []

        def apply_rules_side_effect(transactions, _rules):
            return transactions

        mock_transaction_enhancer.apply_rules.side_effect = apply_rules_side_effect
        mock_enhancement_rule_repository.find_by_normalized_description.return_value = None

        transaction_data = TransactionCreateRequest(
            date=transaction_date,
            description=description,
            amount=amount,
            account_id=account_id,
        )

        result = service.create_transaction(
            transaction_data=transaction_data,
        )

        assert result == sample_transaction
        mock_repository.create_transaction.assert_called_once()

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
        new_account_id = uuid4()

        result = service.update_transaction(
            transaction_id=transaction_id,
            transaction_date=new_date,
            description=new_description,
            amount=new_amount,
            account_id=new_account_id,
        )

        assert result == sample_transaction
        mock_repository.get_by_id.assert_called_once_with(transaction_id)
        mock_repository.update.assert_called_once_with(sample_transaction)
        assert sample_transaction.date == new_date
        assert sample_transaction.description == new_description
        assert sample_transaction.amount == new_amount
        assert sample_transaction.account_id == new_account_id

    def test_update_transaction_not_found(self, service, mock_repository):
        transaction_id = uuid4()
        mock_repository.get_by_id.return_value = None
        result = service.update_transaction(
            transaction_id=transaction_id,
            transaction_date=date(2023, 4, 20),
            description="Updated Transaction",
            amount=Decimal("150.75"),
            account_id=uuid4(),
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

    def test_create_transaction_with_exact_rule_match(
        self,
        service,
        mock_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        category_id = uuid4()
        account_id = uuid4()
        rule = EnhancementRule(
            id=uuid4(),
            normalized_description_pattern="test merchant",
            match_type=MatchType.EXACT,
            category_id=category_id,
            counterparty_account_id=None,
            source=EnhancementRuleSource.MANUAL,
        )

        mock_enhancement_rule_repository.get_all.return_value = [rule]

        def apply_rules_side_effect(transactions, _rules):
            transactions[0].category_id = category_id
            transactions[0].categorization_status = CategorizationStatus.RULE_BASED
            return transactions

        mock_transaction_enhancer.apply_rules.side_effect = apply_rules_side_effect

        created_transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Test Merchant",
            normalized_description="test merchant",
            amount=Decimal("100.50"),
            account_id=account_id,
            category_id=category_id,
            categorization_status=CategorizationStatus.RULE_BASED,
        )
        mock_repository.create_transaction.return_value = created_transaction

        transaction_data = TransactionCreateRequest(
            date=date(2023, 4, 15),
            description="Test Merchant",
            amount=Decimal("100.50"),
            account_id=account_id,
        )

        result = service.create_transaction(transaction_data=transaction_data)

        assert result.category_id == category_id
        assert result.categorization_status == CategorizationStatus.RULE_BASED
        mock_enhancement_rule_repository.get_all.assert_called_once()
        mock_transaction_enhancer.apply_rules.assert_called_once()

    def test_create_transaction_with_prefix_rule_match(
        self,
        service,
        mock_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        category_id = uuid4()
        account_id = uuid4()
        rule = EnhancementRule(
            id=uuid4(),
            normalized_description_pattern="amazon",
            match_type=MatchType.PREFIX,
            category_id=category_id,
            counterparty_account_id=None,
            source=EnhancementRuleSource.MANUAL,
        )

        mock_enhancement_rule_repository.get_all.return_value = [rule]

        def apply_rules_side_effect(transactions, _rules):
            transactions[0].category_id = category_id
            transactions[0].categorization_status = CategorizationStatus.RULE_BASED
            return transactions

        mock_transaction_enhancer.apply_rules.side_effect = apply_rules_side_effect

        created_transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Amazon Prime Subscription",
            normalized_description="amazon prime subscription",
            amount=Decimal("14.99"),
            account_id=account_id,
            category_id=category_id,
            categorization_status=CategorizationStatus.RULE_BASED,
        )
        mock_repository.create_transaction.return_value = created_transaction

        transaction_data = TransactionCreateRequest(
            date=date(2023, 4, 15),
            description="Amazon Prime Subscription",
            amount=Decimal("14.99"),
            account_id=account_id,
        )

        result = service.create_transaction(transaction_data=transaction_data)

        assert result.category_id == category_id
        mock_transaction_enhancer.apply_rules.assert_called_once()

    def test_create_transaction_with_infix_rule_match(
        self,
        service,
        mock_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        category_id = uuid4()
        account_id = uuid4()
        rule = EnhancementRule(
            id=uuid4(),
            normalized_description_pattern="coffee",
            match_type=MatchType.INFIX,
            category_id=category_id,
            counterparty_account_id=None,
            source=EnhancementRuleSource.MANUAL,
        )

        mock_enhancement_rule_repository.get_all.return_value = [rule]

        def apply_rules_side_effect(transactions, _rules):
            transactions[0].category_id = category_id
            transactions[0].categorization_status = CategorizationStatus.RULE_BASED
            return transactions

        mock_transaction_enhancer.apply_rules.side_effect = apply_rules_side_effect

        created_transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Starbucks Coffee Shop",
            normalized_description="starbucks coffee shop",
            amount=Decimal("5.50"),
            account_id=account_id,
            category_id=category_id,
            categorization_status=CategorizationStatus.RULE_BASED,
        )
        mock_repository.create_transaction.return_value = created_transaction

        transaction_data = TransactionCreateRequest(
            date=date(2023, 4, 15),
            description="Starbucks Coffee Shop",
            amount=Decimal("5.50"),
            account_id=account_id,
        )

        result = service.create_transaction(transaction_data=transaction_data)

        assert result.category_id == category_id
        mock_transaction_enhancer.apply_rules.assert_called_once()

    def test_create_transaction_no_rule_match_creates_ai_rule(
        self,
        service,
        mock_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        account_id = uuid4()

        mock_enhancement_rule_repository.get_all.return_value = []
        mock_enhancement_rule_repository.find_by_normalized_description.return_value = None

        def apply_rules_side_effect(transactions, _rules):
            return transactions

        mock_transaction_enhancer.apply_rules.side_effect = apply_rules_side_effect

        created_transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="New Merchant",
            normalized_description="new merchant",
            amount=Decimal("100.50"),
            account_id=account_id,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
        )
        mock_repository.create_transaction.return_value = created_transaction

        transaction_data = TransactionCreateRequest(
            date=date(2023, 4, 15),
            description="New Merchant",
            amount=Decimal("100.50"),
            account_id=account_id,
        )

        service.create_transaction(transaction_data=transaction_data)

        mock_enhancement_rule_repository.find_by_normalized_description.assert_called_once_with("new merchant")
        mock_enhancement_rule_repository.save.assert_called_once()

        saved_rule = mock_enhancement_rule_repository.save.call_args[0][0]
        assert saved_rule.normalized_description_pattern == "new merchant"
        assert saved_rule.match_type == MatchType.EXACT
        assert saved_rule.category_id is None
        assert saved_rule.source == EnhancementRuleSource.AI

    def test_create_transaction_no_duplicate_ai_rule(
        self,
        service,
        mock_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        account_id = uuid4()
        existing_rule = EnhancementRule(
            id=uuid4(),
            normalized_description_pattern="existing merchant",
            match_type=MatchType.EXACT,
            category_id=None,
            counterparty_account_id=None,
            source=EnhancementRuleSource.AI,
        )

        mock_enhancement_rule_repository.get_all.return_value = []
        mock_enhancement_rule_repository.find_by_normalized_description.return_value = existing_rule

        def apply_rules_side_effect(transactions, _rules):
            return transactions

        mock_transaction_enhancer.apply_rules.side_effect = apply_rules_side_effect

        created_transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Existing Merchant",
            normalized_description="existing merchant",
            amount=Decimal("100.50"),
            account_id=account_id,
            categorization_status=CategorizationStatus.UNCATEGORIZED,
        )
        mock_repository.create_transaction.return_value = created_transaction

        transaction_data = TransactionCreateRequest(
            date=date(2023, 4, 15),
            description="Existing Merchant",
            amount=Decimal("100.50"),
            account_id=account_id,
        )

        service.create_transaction(transaction_data=transaction_data)

        mock_enhancement_rule_repository.save.assert_not_called()

    def test_create_transaction_user_category_takes_precedence(
        self,
        service,
        mock_repository,
        mock_enhancement_rule_repository,
        mock_transaction_enhancer,
    ):
        user_category_id = uuid4()
        account_id = uuid4()

        created_transaction = Transaction(
            id=uuid4(),
            date=date(2023, 4, 15),
            description="Test Transaction",
            normalized_description="test transaction",
            amount=Decimal("100.50"),
            account_id=account_id,
            category_id=user_category_id,
            categorization_status=CategorizationStatus.MANUAL,
        )
        mock_repository.create_transaction.return_value = created_transaction

        transaction_data = TransactionCreateRequest(
            date=date(2023, 4, 15),
            description="Test Transaction",
            amount=Decimal("100.50"),
            account_id=account_id,
            category_id=user_category_id,
        )

        result = service.create_transaction(transaction_data=transaction_data)

        assert result.category_id == user_category_id
        mock_enhancement_rule_repository.get_all.assert_not_called()
        mock_transaction_enhancer.apply_rules.assert_not_called()
