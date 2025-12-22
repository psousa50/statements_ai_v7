"""
Integration tests for statement upload that test actual service implementation
with real component interactions. Only external dependencies like LLM are mocked.
"""

import os
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api.schemas import StatementUploadRequest
from app.core.database import Base
from app.core.dependencies import ExternalDependencies, build_internal_dependencies
from app.domain.models.account import Account
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource
from app.domain.models.statement import Statement
from app.domain.models.transaction import Transaction
from app.domain.models.uploaded_file import UploadedFile
from app.domain.models.user import User


@pytest.fixture
def db_engine():
    """Create a test database engine using the DATABASE_URL environment variable."""
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("TEST_DATABASE_URL environment variable not set")

    engine = create_engine(database_url)

    # Ensure the database schema is up to date with current models
    # This will create/update tables based on the current SQLAlchemy models
    Base.metadata.create_all(engine)

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
def test_user(db_session):
    """Create a test user for integration tests."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        oauth_provider="google",
        oauth_id="google-test-user",
    )
    db_session.add(user)
    db_session.flush()
    return user


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

    def test_complete_statement_upload_flow_with_real_services(self, db_session, llm_client, test_user):
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
            user_id=test_user.id,
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
        source = Account(name="Test Bank", user_id=test_user.id)
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
            user_id=test_user.id,
            upload_data=upload_request,
            background_tasks=MagicMock(),
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

        # Step 4: Verify enhancement rules table
        enhancement_rules = db_session.query(EnhancementRule).all()

        # Check if any enhancement rules were created during processing
        for rule in enhancement_rules:
            assert rule.source in [
                EnhancementRuleSource.MANUAL,
                EnhancementRuleSource.AI,
            ]
            assert rule.normalized_description_pattern is not None
            assert len(rule.normalized_description_pattern) > 0
            assert rule.created_at is not None

    def test_upload_with_real_categorization_processing(self, db_session, llm_client, test_user):
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
            user_id=test_user.id,
            filename=filename,
            file_content=csv_content,
        )

        # Create source
        source = Account(name="Credit Card", user_id=test_user.id)
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
            user_id=test_user.id,
            upload_data=upload_request,
            background_tasks=MagicMock(),
            internal_deps=dependencies,
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

        # Verify enhancement rules
        enhancement_rules = db_session.query(EnhancementRule).all()

        # For each rule, verify it has proper structure
        for rule in enhancement_rules:
            assert rule.source in [
                EnhancementRuleSource.MANUAL,
                EnhancementRuleSource.AI,
            ]
            assert rule.normalized_description_pattern is not None
            assert len(rule.normalized_description_pattern) > 0
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

    def test_categorization_source_tracking(self, db_session, llm_client, test_user):
        """Test that categorization sources are properly tracked in the database."""

        filename = "source_test.csv"
        csv_content = b"""Date,Amount,Description
2023-01-01,-25.00,Starbucks Coffee Purchase
2023-01-02,-100.00,Unknown Merchant XYZ"""

        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))

        analysis_result = dependencies.statement_analyzer_service.analyze(
            user_id=test_user.id,
            filename=filename,
            file_content=csv_content,
        )

        source = Account(name="Test Card", user_id=test_user.id)
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
            user_id=test_user.id,
            upload_data=upload_request,
            background_tasks=MagicMock(),
            internal_deps=dependencies,
        )

        # Check enhancement rules in database
        enhancement_rules = db_session.query(EnhancementRule).all()

        # Verify source tracking (if any rules were created)
        if enhancement_rules:
            # All sources should be valid enum values
            valid_sources = {
                EnhancementRuleSource.MANUAL,
                EnhancementRuleSource.AI,
            }
            for rule in enhancement_rules:
                assert rule.source in valid_sources, f"Invalid enhancement rule source: {rule.source}"

            # Verify each enhancement rule has complete data
            for rule in enhancement_rules:
                assert rule.source is not None
                assert rule.normalized_description_pattern is not None
                assert rule.created_at is not None
                # Note: category_id and counterparty_account_id can be None for unmatched rules

    def test_upload_with_row_filters_integration(self, db_session, llm_client, test_user):
        """Test complete upload flow with row filters persisted to file analysis metadata."""

        # CSV content with various amounts to test filtering
        filename = "filtered_statement.csv"
        csv_content = b"""Date,Amount,Description
2023-01-01,50.00,Small Purchase
2023-01-02,150.00,Large Purchase
2023-01-03,25.00,Tiny Purchase
2023-01-04,300.00,Big Purchase"""

        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))

        # Analyze file first
        analysis_result = dependencies.statement_analyzer_service.analyze(
            user_id=test_user.id,
            filename=filename,
            file_content=csv_content,
        )

        # Create account
        account = Account(name="Test Account", user_id=test_user.id)
        db_session.add(account)
        db_session.flush()

        # Create upload request with row filters
        from app.api.schemas import FilterConditionRequest, RowFilterRequest
        from app.domain.dto.statement_processing import FilterOperator, LogicalOperator

        row_filters = RowFilterRequest(
            conditions=[
                FilterConditionRequest(
                    column_name="Amount",
                    operator=FilterOperator.GREATER_THAN,
                    value="100",
                    case_sensitive=False,
                )
            ],
            logical_operator=LogicalOperator.AND,
        )

        upload_request = StatementUploadRequest(
            uploaded_file_id=analysis_result.uploaded_file_id,
            account_id=str(account.id),
            column_mapping=analysis_result.column_mapping,
            header_row_index=analysis_result.header_row_index,
            data_start_row_index=analysis_result.data_start_row_index,
            row_filters=row_filters,
        )

        # Execute upload
        upload_result = dependencies.statement_upload_service.upload_statement(
            user_id=test_user.id,
            upload_data=upload_request,
            background_tasks=MagicMock(),
            internal_deps=dependencies,
        )

        # Verify upload worked and filtered correctly
        # Should only process transactions > 100 (2 transactions: 150.00 and 300.00)
        assert upload_result.transactions_saved == 2
        assert upload_result.total_processed == 2

        # Verify file analysis metadata was saved with row filters
        from app.domain.models.uploaded_file import FileAnalysisMetadata

        metadata = db_session.query(FileAnalysisMetadata).first()
        assert metadata is not None
        assert metadata.row_filters is not None
        # Verify the saved row filters have the expected structure
        assert isinstance(metadata.row_filters, list)
        assert len(metadata.row_filters) > 0
        saved_filter = metadata.row_filters[0]
        assert saved_filter["column_name"] == "Amount"
        assert saved_filter["operator"] == "greater_than"
        assert saved_filter["value"] == "100"

        # Verify the actual transactions saved match the filter
        statement = db_session.query(Statement).filter(Statement.account_id == account.id).first()
        assert statement is not None

        transactions = db_session.query(Transaction).filter(Transaction.statement_id == statement.id).all()
        assert len(transactions) == 2

        # Verify only large amounts were saved
        amounts = [float(t.amount) for t in transactions]
        assert 150.00 in amounts
        assert 300.00 in amounts
        assert 50.00 not in amounts  # Filtered out
        assert 25.00 not in amounts  # Filtered out

    def test_upload_without_row_filters_persists_null(self, db_session, llm_client, test_user):
        """Test that uploads without row filters persist NULL in the database."""

        filename = "no_filters.csv"
        csv_content = b"""Date,Amount,Description
2023-01-01,100.00,Test Transaction"""

        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))

        analysis_result = dependencies.statement_analyzer_service.analyze(
            user_id=test_user.id,
            filename=filename,
            file_content=csv_content,
        )

        account = Account(name="No Filter Account", user_id=test_user.id)
        db_session.add(account)
        db_session.flush()

        # Upload request without row filters
        upload_request = StatementUploadRequest(
            uploaded_file_id=analysis_result.uploaded_file_id,
            account_id=str(account.id),
            column_mapping=analysis_result.column_mapping,
            header_row_index=analysis_result.header_row_index,
            data_start_row_index=analysis_result.data_start_row_index,
        )

        dependencies.statement_upload_service.upload_statement(
            user_id=test_user.id,
            upload_data=upload_request,
            background_tasks=MagicMock(),
            internal_deps=dependencies,
        )

        # Verify file analysis metadata has null row_filters
        from app.domain.models.uploaded_file import FileAnalysisMetadata

        metadata = db_session.query(FileAnalysisMetadata).first()
        assert metadata is not None
        assert metadata.row_filters is None

    def test_duplicate_file_upload_reuses_saved_row_filters(self, db_session, llm_client, test_user):
        """Test that uploading the same file again automatically applies saved row filters."""

        # Step 1: Upload file WITH row filters first time
        filename = "reuse_filters.csv"
        csv_content = b"""Date,Amount,Description
2023-01-01,50.00,Small Purchase
2023-01-02,150.00,Large Purchase
2023-01-03,25.00,Tiny Purchase
2023-01-04,300.00,Big Purchase"""

        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))

        # First analysis
        analysis_result = dependencies.statement_analyzer_service.analyze(
            user_id=test_user.id,
            filename=filename,
            file_content=csv_content,
        )

        account = Account(name="Reuse Test Account", user_id=test_user.id)
        db_session.add(account)
        db_session.flush()

        # First upload WITH row filters
        from app.api.schemas import FilterConditionRequest, RowFilterRequest
        from app.domain.dto.statement_processing import FilterOperator, LogicalOperator

        row_filters = RowFilterRequest(
            conditions=[
                FilterConditionRequest(
                    column_name="Amount", operator=FilterOperator.GREATER_THAN, value="100", case_sensitive=False
                )
            ],
            logical_operator=LogicalOperator.AND,
        )

        first_upload_request = StatementUploadRequest(
            uploaded_file_id=analysis_result.uploaded_file_id,
            account_id=str(account.id),
            column_mapping=analysis_result.column_mapping,
            header_row_index=analysis_result.header_row_index,
            data_start_row_index=analysis_result.data_start_row_index,
            row_filters=row_filters,
        )

        first_result = dependencies.statement_upload_service.upload_statement(
            user_id=test_user.id,
            upload_data=first_upload_request,
            background_tasks=MagicMock(),
            internal_deps=dependencies,
        )

        # Verify first upload: 2 transactions saved (150.00 and 300.00)
        assert first_result.transactions_saved == 2
        assert first_result.total_processed == 2

        # Step 2: Upload the SAME file again WITHOUT specifying row filters
        # Analyze the same file again (new upload)
        second_analysis_result = dependencies.statement_analyzer_service.analyze(
            user_id=test_user.id,
            filename=filename,
            file_content=csv_content,
        )

        # Second upload WITHOUT row filters in request
        second_upload_request = StatementUploadRequest(
            uploaded_file_id=second_analysis_result.uploaded_file_id,
            account_id=str(account.id),
            column_mapping=second_analysis_result.column_mapping,
            header_row_index=second_analysis_result.header_row_index,
            data_start_row_index=second_analysis_result.data_start_row_index,
        )

        second_result = dependencies.statement_upload_service.upload_statement(
            user_id=test_user.id,
            upload_data=second_upload_request,
            background_tasks=MagicMock(),
            internal_deps=dependencies,
        )

        # Verify second upload: Row filters applied (total_processed=2) but transactions are duplicates (saved=0)
        assert second_result.total_processed == 2  # Row filters were applied correctly
        assert second_result.transactions_saved == 0  # Transactions detected as duplicates (correct behavior)

        # Verify that the saved row filters were reused
        from app.domain.models.uploaded_file import FileAnalysisMetadata

        metadata = db_session.query(FileAnalysisMetadata).first()
        assert metadata is not None
        assert metadata.row_filters is not None
        assert len(metadata.row_filters) == 1
        assert metadata.row_filters[0]["column_name"] == "Amount"
        assert metadata.row_filters[0]["operator"] == "greater_than"
        assert metadata.row_filters[0]["value"] == "100"

        # Verify two statements exist (different uploaded files) but only first has transactions
        statements = db_session.query(Statement).filter(Statement.account_id == account.id).all()
        assert len(statements) == 2  # Two statements (different uploaded files)

        # Find which statement has transactions and which doesn't
        statement_with_transactions = None
        statement_without_transactions = None

        for statement in statements:
            transactions = db_session.query(Transaction).filter(Transaction.statement_id == statement.id).all()
            if len(transactions) > 0:
                statement_with_transactions = statement
            else:
                statement_without_transactions = statement

        # Verify we have one statement with transactions and one without
        assert statement_with_transactions is not None
        assert statement_without_transactions is not None

        # Verify the first statement has the correctly filtered transactions
        transactions = db_session.query(Transaction).filter(Transaction.statement_id == statement_with_transactions.id).all()
        assert len(transactions) == 2
        amounts = [float(t.amount) for t in transactions]
        assert 150.00 in amounts
        assert 300.00 in amounts
        assert 50.00 not in amounts  # Filtered out
        assert 25.00 not in amounts  # Filtered out

        # Verify the second statement has no transactions (duplicates were filtered out)
        empty_transactions = (
            db_session.query(Transaction).filter(Transaction.statement_id == statement_without_transactions.id).all()
        )
        assert len(empty_transactions) == 0
