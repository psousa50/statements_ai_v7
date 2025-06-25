"""
Integration tests for statement upload that test actual service implementation
with real component interactions. Only external dependencies like LLM are mocked.
"""

import os
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api.schemas import StatementUploadRequest
from app.core.dependencies import ExternalDependencies, build_internal_dependencies
from app.domain.models.account import Account
from app.domain.models.statement import Statement
from app.domain.models.transaction import Transaction
from app.domain.models.transaction_categorization import CategorizationSource, TransactionCategorization
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
        "column_mapping": {
            "date": "Date",
            "amount": "Amount", 
            "description": "Description"
        },
        "header_row_index": 0,
        "data_start_row_index": 1
    }
    """

    # Mock categorization responses
    llm_client.categorize_transaction.return_value = {
        "category": "Food & Dining",
        "confidence": 0.85,
    }

    return llm_client


@pytest.mark.integration
class TestStatementUploadIntegration:
    """Integration tests using real service implementations with actual database."""

    def test_complete_statement_upload_flow_with_real_services(self, db_session, llm_client):
        """Test complete upload flow: analyze → upload → process → persist."""

        # Real CSV content
        filename = "bank_statement.csv"
        csv_content = b"""Date,Amount,Description,Balance
2023-01-01,100.50,Coffee Shop Purchase,1500.50
2023-01-02,-50.00,ATM Withdrawal,1450.50  
2023-01-03,2500.00,Salary Deposit,3950.50
2023-01-04,-25.99,Online Shopping,3924.51"""

        # Build real dependencies (only LLM is mocked)
        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))

        # Step 1: Real file analysis
        analysis_result = dependencies.statement_analyzer_service.analyze(
            filename=filename,
            file_content=csv_content,
        )

        # Verify real analysis worked
        assert analysis_result.uploaded_file_id is not None
        assert analysis_result.file_type == "CSV"
        assert analysis_result.column_mapping["date"] == "Date"
        assert analysis_result.column_mapping["amount"] == "Amount"
        assert analysis_result.column_mapping["description"] == "Description"
        assert len(analysis_result.sample_data) > 0

        # Create a real source
        source = Account(name="Test Bank")
        db_session.add(source)
        db_session.flush()

        # Step 2: Real statement upload with processing
        upload_request = StatementUploadRequest(
            uploaded_file_id=analysis_result.uploaded_file_id,
            account_id=str(source.id),
            column_mapping=analysis_result.column_mapping,
            header_row_index=analysis_result.header_row_index,
            data_start_row_index=analysis_result.data_start_row_index,
        )

        # Use real upload service
        upload_result = dependencies.statement_upload_service.upload_statement(
            upload_request,
            background_tasks=MagicMock(),  # Mock FastAPI background tasks
            internal_deps=dependencies,
        )

        # Verify upload results
        assert upload_result.uploaded_file_id == analysis_result.uploaded_file_id
        assert upload_result.transactions_saved == 4
        assert upload_result.total_processed == 4
        assert upload_result.processing_time_ms > 0

        # Step 3: Verify real database persistence
        uploaded_file_id = analysis_result.uploaded_file_id

        # Check uploaded file was saved
        uploaded_file = db_session.query(UploadedFile).filter(UploadedFile.id == uploaded_file_id).first()
        assert uploaded_file is not None
        assert uploaded_file.filename == filename
        assert uploaded_file.content == csv_content

        # Check transactions were actually saved to database
        # Get the statement that was created for this account
        statement = db_session.query(Statement).filter(Statement.account_id == source.id).first()
        assert statement is not None

        transactions = db_session.query(Transaction).filter(Transaction.statement_id == statement.id).all()
        assert len(transactions) == 4

        # Verify specific transaction data
        amounts = [float(t.amount) for t in transactions]
        descriptions = [t.description for t in transactions]

        assert 100.50 in amounts
        assert -50.00 in amounts
        assert 2500.00 in amounts
        assert -25.99 in amounts

        assert any("Coffee Shop" in desc for desc in descriptions)
        assert any("ATM" in desc for desc in descriptions)
        assert any("Salary" in desc for desc in descriptions)

        # Step 4: Verify transaction categorization table
        categorization_rules = db_session.query(TransactionCategorization).all()

        # Check if any categorization rules were created during processing
        for rule in categorization_rules:
            assert rule.category_id is not None
            assert rule.source in [CategorizationSource.MANUAL, CategorizationSource.AI]
            assert rule.normalized_description is not None
            assert len(rule.normalized_description) > 0
            assert rule.created_at is not None

    def test_upload_with_real_categorization_processing(self, db_session, llm_client):
        """Test upload with real transaction categorization flow."""

        # CSV with categorizable transactions
        filename = "transactions.csv"
        csv_content = b"""Date,Amount,Description
2023-01-01,-15.50,McDonald's Restaurant
2023-01-02,-45.00,Uber Ride Downtown
2023-01-03,-120.00,Grocery Store Purchase"""

        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))

        # Analyze file
        analysis_result = dependencies.statement_analyzer_service.analyze(
            filename=filename,
            file_content=csv_content,
        )

        # Create source
        source = Account(name="Credit Card")
        db_session.add(source)
        db_session.flush()

        # Upload and process
        upload_request = StatementUploadRequest(
            uploaded_file_id=analysis_result.uploaded_file_id,
            account_id=str(source.id),
            column_mapping=analysis_result.column_mapping,
            header_row_index=analysis_result.header_row_index,
            data_start_row_index=analysis_result.data_start_row_index,
        )

        upload_result = dependencies.statement_upload_service.upload_statement(
            upload_request, background_tasks=MagicMock(), internal_deps=dependencies
        )

        # Verify processing worked
        assert upload_result.total_processed == 3
        assert upload_result.transactions_saved == 3

        # Check real database state
        # Get the statement that was created for this account
        statement = db_session.query(Statement).filter(Statement.account_id == source.id).first()
        assert statement is not None

        transactions = db_session.query(Transaction).filter(Transaction.statement_id == statement.id).all()

        assert len(transactions) == 3
        # Verify all transactions have normalized descriptions (processed by real normalizer)
        assert all(t.normalized_description is not None for t in transactions)
        assert all(len(t.normalized_description) > 0 for t in transactions)

        # Verify transaction categorization rules
        categorization_rules = db_session.query(TransactionCategorization).all()

        # For each rule, verify it has proper structure
        for rule in categorization_rules:
            assert rule.category_id is not None
            assert rule.source in [CategorizationSource.MANUAL, CategorizationSource.AI]
            assert rule.normalized_description is not None
            assert len(rule.normalized_description) > 0
            assert rule.created_at is not None

        # Verify transactions have proper categorization status
        for transaction in transactions:
            # Transaction should have a categorization status
            assert hasattr(transaction, "categorization_status")
            # Should be either UNCATEGORIZED, CATEGORIZED, or FAILURE
            assert transaction.categorization_status.value in [
                "UNCATEGORIZED",
                "CATEGORIZED",
                "FAILURE",
            ]

    def test_categorization_source_tracking(self, db_session, llm_client):
        """Test that categorization sources are properly tracked in the database."""

        filename = "source_test.csv"
        csv_content = b"""Date,Amount,Description
2023-01-01,-25.00,Starbucks Coffee Purchase
2023-01-02,-100.00,Unknown Merchant XYZ"""

        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))

        analysis_result = dependencies.statement_analyzer_service.analyze(
            filename=filename,
            file_content=csv_content,
        )

        source = Account(name="Test Card")
        db_session.add(source)
        db_session.flush()

        upload_request = StatementUploadRequest(
            uploaded_file_id=analysis_result.uploaded_file_id,
            account_id=str(source.id),
            column_mapping=analysis_result.column_mapping,
            header_row_index=analysis_result.header_row_index,
            data_start_row_index=analysis_result.data_start_row_index,
        )

        dependencies.statement_upload_service.upload_statement(
            upload_request, background_tasks=MagicMock(), internal_deps=dependencies
        )

        # Check categorization rules in database
        categorization_rules = db_session.query(TransactionCategorization).all()

        # Verify source tracking (if any rules were created)
        if categorization_rules:
            # All sources should be valid enum values
            valid_sources = {CategorizationSource.MANUAL, CategorizationSource.AI}
            for rule in categorization_rules:
                assert rule.source in valid_sources, f"Invalid categorization source: {rule.source}"

            # Verify each categorization rule has complete data
            for rule in categorization_rules:
                assert rule.category_id is not None
                assert rule.source is not None
                assert rule.normalized_description is not None
                assert rule.created_at is not None
