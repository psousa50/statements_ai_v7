import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import CategorizationStatus


class TestSQLAlchemyTransactionRepository:
    def test_save_batch_persists_enhancement_fields(self):
        session = MagicMock()
        repo = SQLAlchemyTransactionRepository(session)

        account_id = uuid.uuid4()
        statement_id = uuid.uuid4()
        category_id = uuid.uuid4()
        counterparty_id = uuid.uuid4()

        transaction_dto = TransactionDTO(
            date="2025-09-29",
            amount=Decimal("-226.00"),
            description="TRF P/ TITINA",
            account_id=str(account_id),
            statement_id=str(statement_id),
            row_index=0,
            sort_index=0,
            source_type="UPLOAD",
            category_id=str(category_id),
            counterparty_account_id=str(counterparty_id),
            categorization_status=CategorizationStatus.RULE_BASED,
        )

        session.query.return_value.filter.return_value.all.return_value = []

        saved_count, duplicates_count = repo.save_batch([transaction_dto])

        assert saved_count == 1
        assert duplicates_count == 0

        session.add.assert_called_once()
        saved_transaction = session.add.call_args[0][0]

        assert saved_transaction.date == date(2025, 9, 29)
        assert saved_transaction.amount == Decimal("-226.00")
        assert saved_transaction.description == "TRF P/ TITINA"
        assert saved_transaction.normalized_description == "trf p titina"
        assert saved_transaction.account_id == account_id
        assert saved_transaction.statement_id == statement_id
        assert saved_transaction.category_id == category_id
        assert saved_transaction.counterparty_account_id == counterparty_id
        assert saved_transaction.categorization_status == CategorizationStatus.RULE_BASED

        session.commit.assert_called_once()

    def test_save_batch_handles_none_enhancement_fields(self):
        session = MagicMock()
        repo = SQLAlchemyTransactionRepository(session)

        account_id = uuid.uuid4()
        statement_id = uuid.uuid4()

        transaction_dto = TransactionDTO(
            date="2025-09-29",
            amount=Decimal("-100.00"),
            description="Some transaction",
            account_id=str(account_id),
            statement_id=str(statement_id),
            row_index=0,
            sort_index=0,
            source_type="UPLOAD",
            category_id=None,
            counterparty_account_id=None,
            categorization_status=None,
        )

        session.query.return_value.filter.return_value.all.return_value = []

        saved_count, duplicates_count = repo.save_batch([transaction_dto])

        assert saved_count == 1
        assert duplicates_count == 0

        session.add.assert_called_once()
        saved_transaction = session.add.call_args[0][0]

        assert saved_transaction.category_id is None
        assert saved_transaction.counterparty_account_id is None
        assert saved_transaction.categorization_status == CategorizationStatus.UNCATEGORIZED

        session.commit.assert_called_once()

    def test_save_batch_skips_duplicates(self):
        session = MagicMock()
        repo = SQLAlchemyTransactionRepository(session)

        account_id = uuid.uuid4()
        statement_id = uuid.uuid4()

        transaction_dto = TransactionDTO(
            date="2025-09-29",
            amount=Decimal("-226.00"),
            description="TRF P/ TITINA",
            account_id=str(account_id),
            statement_id=str(statement_id),
            row_index=0,
            sort_index=0,
            source_type="UPLOAD",
        )

        existing_transaction = MagicMock()
        existing_transaction.id = uuid.uuid4()

        def mock_find_matching(date, description, amount, account_id):
            return [existing_transaction]

        repo.find_matching_transactions = mock_find_matching

        saved_count, duplicates_count = repo.save_batch([transaction_dto])

        assert saved_count == 0
        assert duplicates_count == 1

        session.add.assert_not_called()
        session.commit.assert_called_once()
