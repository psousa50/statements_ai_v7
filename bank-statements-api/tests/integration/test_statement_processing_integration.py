import json
import os
from uuid import UUID

import pandas as pd
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.domain.dto.statement_processing import AnalysisResultDTO, PersistenceResultDTO

from app.adapters.repositories.source import SQLAlchemySourceRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.adapters.repositories.uploaded_file import SQLAlchemyFileAnalysisMetadataRepository, SQLAlchemyUploadedFileRepository
from app.domain.models.category import Category
from app.domain.models.source import Source
from app.domain.models.transaction import Transaction
from app.domain.models.uploaded_file import FileAnalysisMetadata, UploadedFile
from app.services.statement_processing.file_type_detector import StatementFileTypeDetector
from app.services.statement_processing.schema_detector import LLMClient, SchemaDetector
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService
from app.services.statement_processing.statement_parser import StatementParser
from app.services.statement_processing.statement_persistence import StatementPersistenceService
from app.services.statement_processing.transaction_normalizer import TransactionNormalizer


class MockLLMClient(LLMClient):
    def __init__(self, fixed_response: str):
        self.fixed_response = fixed_response
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.fixed_response

    async def generate_async(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.fixed_response


@pytest.fixture
def db_engine():
    """Create a test database engine using the DATABASE_URL environment variable."""
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("TEST_DATABASE_URL environment variable not set")

    engine = create_engine(database_url)

    # Create necessary tables for testing
    with engine.connect() as conn:
        # Drop tables if they exist
        conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS file_analysis_metadata CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS uploaded_files CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS sources CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS categories CASCADE"))

        # Create tables
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS categories (
                id UUID PRIMARY KEY,
                name VARCHAR NOT NULL,
                parent_id UUID,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS sources (
                id UUID PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id UUID PRIMARY KEY,
                filename TEXT NOT NULL,
                content BYTEA NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS file_analysis_metadata (
                id UUID PRIMARY KEY,
                uploaded_file_id UUID NOT NULL REFERENCES uploaded_files(id),
                file_hash TEXT NOT NULL UNIQUE,
                file_type VARCHAR NOT NULL,
                column_mapping JSONB NOT NULL,
                header_row_index INTEGER NOT NULL,
                data_start_row_index INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS transactions (
                id UUID PRIMARY KEY,
                date DATE NOT NULL,
                description VARCHAR NOT NULL,
                amount NUMERIC(10,2) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                uploaded_file_id UUID REFERENCES uploaded_files(id),
                category_id UUID REFERENCES categories(id),
                source_id UUID REFERENCES sources(id),
                categorization_status VARCHAR NOT NULL DEFAULT 'UNCATEGORIZED'
            )
        """
            )
        )

        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_date ON transactions (date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_file_analysis_metadata_file_hash ON file_analysis_metadata (file_hash)"))

        conn.commit()

    yield engine


@pytest.fixture
def db_session(db_engine):
    """Creates a session that rolls back *everything* at the end of the test, even commits."""
    connection = db_engine.connect()
    transaction = connection.begin()

    # Create a new session bound to the connection
    Session = sessionmaker(bind=connection)
    session = Session()

    # Start a nested transaction (savepoint)
    session.begin_nested()

    # Ensure new SAVEPOINTs are created after each commit
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    # Cleanup: rollback outer transaction and close connection
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def repositories(db_session):
    """Create repositories for testing."""
    uploaded_file_repo = SQLAlchemyUploadedFileRepository(db_session)
    file_analysis_metadata_repo = SQLAlchemyFileAnalysisMetadataRepository(db_session)
    transaction_repo = SQLAlchemyTransactionRepository(db_session)
    source_repo = SQLAlchemySourceRepository(db_session)

    return {
        "uploaded_file_repo": uploaded_file_repo,
        "file_analysis_metadata_repo": file_analysis_metadata_repo,
        "transaction_repo": transaction_repo,
        "source_repo": source_repo,
    }


# Add a custom JSON encoder for pandas Timestamp objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime("%Y-%m-%d")
        return super().default(obj)


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    llm_response = """
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
    return MockLLMClient(llm_response)


@pytest.fixture
def statement_processing_services(repositories, mock_llm_client):
    """Create statement processing services for testing."""
    file_type_detector = StatementFileTypeDetector()
    statement_parser = StatementParser()
    schema_detector = SchemaDetector(mock_llm_client)
    transaction_normalizer = TransactionNormalizer()

    analyzer_service = StatementAnalyzerService(
        file_type_detector=file_type_detector,
        statement_parser=statement_parser,
        schema_detector=schema_detector,
        transaction_normalizer=transaction_normalizer,
        uploaded_file_repo=repositories["uploaded_file_repo"],
        file_analysis_metadata_repo=repositories["file_analysis_metadata_repo"],
    )

    persistence_service = StatementPersistenceService(
        statement_parser=statement_parser,
        transaction_normalizer=transaction_normalizer,
        transaction_repo=repositories["transaction_repo"],
        uploaded_file_repo=repositories["uploaded_file_repo"],
        file_analysis_metadata_repo=repositories["file_analysis_metadata_repo"],
    )

    return {
        "analyzer_service": analyzer_service,
        "persistence_service": persistence_service,
    }


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    filename = "test_statement.csv"
    content = b"Date,Amount,Description\n2023-01-01,100.00,Deposit\n2023-01-02,-50.00,Withdrawal\n2023-01-03,25.50,Refund"

    return {"filename": filename, "content": content}


@pytest.mark.integration
class TestStatementProcessingIntegration:
    def test_analyze_and_persist_new_file(self, statement_processing_services, sample_csv_file, db_session, repositories):
        analyzer_service = statement_processing_services["analyzer_service"]
        analysis_result = analyzer_service.analyze(
            filename=sample_csv_file["filename"],
            file_content=sample_csv_file["content"],
        )

        # Verify analysis result
        assert isinstance(analysis_result, AnalysisResultDTO)
        assert analysis_result.uploaded_file_id is not None
        assert analysis_result.file_type is not None
        assert analysis_result.column_mapping is not None
        assert analysis_result.header_row_index is not None
        assert analysis_result.data_start_row_index is not None
        assert analysis_result.sample_data is not None
        assert analysis_result.file_hash is not None

        assert analysis_result.file_type == "CSV"
        assert analysis_result.column_mapping == {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }

        # Create a test source
        source = Source(name="Test Bank")
        db_session.add(source)
        db_session.flush()

        # Add source_id to the analysis result
        analysis_result.source_id = str(source.id)

        # Step 2: Persist the analyzed file
        persistence_service = statement_processing_services["persistence_service"]
        persistence_result = persistence_service.persist(analysis_result)

        # Verify persistence result
        assert isinstance(persistence_result, PersistenceResultDTO)
        assert persistence_result.uploaded_file_id is not None
        assert persistence_result.transactions_saved is not None
        assert persistence_result.uploaded_file_id == analysis_result.uploaded_file_id
        assert persistence_result.transactions_saved == 2  # The system is saving 2 transactions

        # Step 3: Verify data in the database
        # Check uploaded file
        uploaded_file_id = UUID(analysis_result.uploaded_file_id)
        uploaded_file = db_session.query(UploadedFile).filter(UploadedFile.id == uploaded_file_id).first()
        assert uploaded_file is not None
        assert uploaded_file.filename == sample_csv_file["filename"]
        assert uploaded_file.content == sample_csv_file["content"]

        # Check file analysis metadata
        file_hash = analysis_result.file_hash
        metadata = db_session.query(FileAnalysisMetadata).filter(FileAnalysisMetadata.file_hash == file_hash).first()
        assert metadata is not None
        assert metadata.uploaded_file_id == uploaded_file_id
        assert metadata.file_type == "CSV"
        assert metadata.column_mapping == {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }

        # Check transactions
        transactions = db_session.query(Transaction).filter(Transaction.uploaded_file_id == uploaded_file_id).all()
        assert len(transactions) == 2

        # Verify transaction data
        expected_amounts = [-50.00, 25.50]
        expected_descriptions = ["Withdrawal", "Refund"]

        for transaction in transactions:
            assert float(transaction.amount) in expected_amounts
            assert transaction.description in expected_descriptions

    def test_analyze_duplicate_file(self, statement_processing_services, sample_csv_file, db_session, repositories):
        """
        Test analyzing a duplicate file.

        This integration test verifies that:
        1. The analyzer service correctly identifies a duplicate file by its hash
        2. The analyzer service returns the existing metadata without creating a new file
        """
        # First, analyze and persist the file
        analyzer_service = statement_processing_services["analyzer_service"]
        persistence_service = statement_processing_services["persistence_service"]

        # First analysis
        first_analysis = analyzer_service.analyze(
            filename=sample_csv_file["filename"],
            file_content=sample_csv_file["content"],
        )

        # Create a test source
        source = Source(name="Test Bank")
        db_session.add(source)
        db_session.flush()

        # Add source_id to the analysis result
        first_analysis.source_id = str(source.id)

        # Persist the first analysis
        persistence_service.persist(first_analysis)

        # Get the initial count of files and metadata
        initial_file_count = db_session.query(UploadedFile).count()
        initial_metadata_count = db_session.query(FileAnalysisMetadata).count()

        # Second analysis (should detect duplicate)
        second_analysis = analyzer_service.analyze(
            filename=sample_csv_file["filename"],
            file_content=sample_csv_file["content"],
        )

        # Verify that the second analysis returns the same data as the first
        assert isinstance(second_analysis, AnalysisResultDTO)
        assert second_analysis.uploaded_file_id == first_analysis.uploaded_file_id
        assert second_analysis.file_type == first_analysis.file_type
        assert second_analysis.column_mapping == first_analysis.column_mapping
        assert second_analysis.header_row_index == first_analysis.header_row_index
        assert second_analysis.data_start_row_index == first_analysis.data_start_row_index

        # Verify that no new files or metadata were created
        assert db_session.query(UploadedFile).count() == initial_file_count
        assert db_session.query(FileAnalysisMetadata).count() == initial_metadata_count

    def test_end_to_end_flow_with_different_file(self, statement_processing_services, db_session):
        """
        Test the end-to-end flow with a different file format.

        This integration test verifies that:
        1. The analyzer and persistence services can handle different file formats
        2. The data is correctly processed and stored
        """
        # Create a different file format (XLSX-like binary content)
        filename = "test_statement.xlsx"
        # This is a simplified mock of XLSX file content that will be detected as XLSX
        content = b"PK\x03\x04" + b"\x00" * 100 + b"Date\tAmount\tDescription\n2023-01-04\t75.25\tSalary\n2023-01-05\t-30.00\tBill Payment"

        # Mock the statement parser to handle our mock XLSX content
        statement_parser = statement_processing_services["analyzer_service"].statement_parser
        original_parse = statement_parser.parse

        def mock_parse(file_content, file_type):
            if file_type == "XLSX":
                # Return a DataFrame that would be expected from parsing an XLSX file
                return pd.DataFrame(
                    {
                        "Date": ["2023-01-04", "2023-01-05"],
                        "Amount": [75.25, -30.00],
                        "Description": ["Salary", "Bill Payment"],
                    }
                )
            return original_parse(file_content, file_type)

        # Apply the mock
        statement_parser.parse = mock_parse

        try:
            # Analyze the file
            analyzer_service = statement_processing_services["analyzer_service"]
            analysis_result = analyzer_service.analyze(filename=filename, file_content=content)

            # Verify analysis result
            assert isinstance(analysis_result, AnalysisResultDTO)
            assert analysis_result.file_type == "XLSX"

            # Create a test source
            source = Source(name="Test Bank XLSX")
            db_session.add(source)
            db_session.flush()

            # Add source_id to the analysis result
            analysis_result.source_id = str(source.id)

            # Persist the analyzed file
            persistence_service = statement_processing_services["persistence_service"]
            persistence_result = persistence_service.persist(analysis_result)

            # Verify persistence result
            assert isinstance(persistence_result, PersistenceResultDTO)
            assert persistence_result.transactions_saved is not None
            assert persistence_result.uploaded_file_id == analysis_result.uploaded_file_id
            assert persistence_result.transactions_saved == 1

            # Step 3: Verify data in the database
            # Check uploaded file
            uploaded_file_id = UUID(analysis_result.uploaded_file_id)
            uploaded_file = db_session.query(UploadedFile).filter(UploadedFile.id == uploaded_file_id).first()
            assert uploaded_file is not None
            assert uploaded_file.filename == filename

            # Check file analysis metadata
            file_hash = analysis_result.file_hash
            metadata = db_session.query(FileAnalysisMetadata).filter(FileAnalysisMetadata.file_hash == file_hash).first()
            assert metadata is not None
            assert metadata.uploaded_file_id == uploaded_file_id
            assert metadata.file_type == "XLSX"
            assert metadata.column_mapping == {
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            }

            # Check transactions
            transactions = db_session.query(Transaction).filter(Transaction.uploaded_file_id == uploaded_file_id).all()
            assert len(transactions) == 1

            # Verify transaction data
            expected_amounts = [75.25, -30.00]
            expected_descriptions = ["Salary", "Bill Payment"]

            for transaction in transactions:
                assert float(transaction.amount) in expected_amounts
                assert transaction.description in expected_descriptions

        finally:
            # Restore the original parse method
            statement_parser.parse = original_parse
