import os
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.dependencies import ExternalDependencies, build_internal_dependencies
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.source import Source
from app.domain.models.transaction import Transaction
from app.domain.models.uploaded_file import UploadedFile


@pytest.fixture
def db_engine():
    """Create a test database engine using the DATABASE_URL environment variable."""
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("TEST_DATABASE_URL environment variable not set")

    engine = create_engine(database_url)
    yield engine


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def llm_client():
    """Mock LLM client for integration tests."""
    llm_client = MagicMock()
    # Mock schema detection response
    llm_client.generate.return_value = """
    {
        "column_map": {
            "date": "Date",
            "amount": "Amount", 
            "description": "Description"
        },
        "header_row": 0,
        "start_row": 1
    }
    """

    # Mock categorization responses
    llm_client.categorize_transaction.return_value = {
        "category": "Food & Dining",
        "confidence": 0.85,
    }

    return llm_client


@pytest.mark.integration
class TestTransactionDeduplicationIntegration:
    def test_transaction_deduplication_end_to_end(self, db_session, llm_client):
        """Test that transaction deduplication works correctly in the complete flow"""
        # Setup dependencies using the same pattern as other integration tests
        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))

        # Create a test source
        source = Source(name="Test Bank for Deduplication")
        db_session.add(source)
        db_session.commit()
        db_session.refresh(source)

        # Create an uploaded file to satisfy foreign key constraint
        uploaded_file_id = uuid.uuid4()
        uploaded_file = UploadedFile(
            id=uploaded_file_id,
            filename="test.csv",
            content=b"Date,Amount,Description\n2023-01-01,25.50,Coffee Shop Purchase",
            file_type="CSV",
        )
        db_session.add(uploaded_file)
        db_session.commit()

        # Create an existing transaction in the database
        existing_transaction = Transaction(
            date=date(2023, 1, 1),
            description="Coffee Shop Purchase",
            amount=Decimal("25.50"),
            source_id=source.id,
            normalized_description="coffee shop purchase",
            uploaded_file_id=uploaded_file_id,
        )
        db_session.add(existing_transaction)
        db_session.commit()

        # Create transaction DTOs with one duplicate and one new transaction
        transaction_dtos = [
            TransactionDTO(
                date="2023-01-01",
                description="Coffee Shop Purchase",  # This is a duplicate
                amount=25.50,
                source_id=str(source.id),
                uploaded_file_id=str(uploaded_file_id),
            ),
            TransactionDTO(
                date="2023-01-02",
                description="Grocery Store",  # This is new
                amount=45.75,
                source_id=str(source.id),
                uploaded_file_id=str(uploaded_file_id),
            ),
            TransactionDTO(
                date="2023-01-03",
                description="Gas Station",  # This is new
                amount=35.00,
                source_id=str(source.id),
                uploaded_file_id=str(uploaded_file_id),
            ),
        ]

        # Use the persistence service to save transactions with deduplication
        persistence_result = dependencies.statement_persistence_service.save_processed_transactions(
            processed_dtos=transaction_dtos,
            source_id=source.id,
            uploaded_file_id=str(uploaded_file_id),
        )

        # Verify the results
        assert persistence_result.transactions_saved == 2  # Only 2 new transactions saved
        assert persistence_result.duplicated_transactions == 1  # 1 duplicate found

        # Verify the database state
        all_transactions = db_session.query(Transaction).filter(Transaction.source_id == source.id).all()
        assert len(all_transactions) == 3  # 1 existing + 2 new

        # Verify the specific transactions
        descriptions = [t.description for t in all_transactions]
        assert "Coffee Shop Purchase" in descriptions  # Original exists
        assert "Grocery Store" in descriptions  # New transaction saved
        assert "Gas Station" in descriptions  # New transaction saved

        # Verify amounts
        amounts = [float(t.amount) for t in all_transactions]
        assert 25.50 in amounts
        assert 45.75 in amounts
        assert 35.00 in amounts
