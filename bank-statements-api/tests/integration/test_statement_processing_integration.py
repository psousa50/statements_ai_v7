import os
from collections import Counter
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.dependencies import ExternalDependencies, build_internal_dependencies
from app.domain.dto.statement_processing import PersistenceRequestDTO, PersistenceResultDTO
from app.domain.models.source import Source
from app.domain.models.transaction import Transaction
from app.domain.models.uploaded_file import FileAnalysisMetadata, UploadedFile


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
def sample_csv_file():
    """Create a sample CSV file for testing."""
    filename = "test_statement.csv"
    csv_content = [
        ["Header 1", "Header 2", "Header 3"],
        ["Data", "Valor", "Descricao"],
        ["2023-01-01", "100.00", "Deposit"],
        ["2023-01-02", "-50.00", "Withdrawal"],
        ["2023-01-03", "25.50", "Refund"],
    ]
    content = "\n".join([",".join(row) for row in csv_content])
    content = content.encode("utf-8")

    return {"filename": filename, "content": content}


@pytest.fixture
def llm_client():
    llm_client = MagicMock()
    llm_client.generate.return_value = """
    {
        "column_map": {
            "date": "Data",
            "amount": "Valor",
            "description": "Descricao"
        },
        "header_row": 1,
        "start_row": 3
    }
    """
    return llm_client


@pytest.mark.integration
class TestStatementProcessingIntegration:
    def test_analyze_and_persist_new_file(self, db_session, sample_csv_file, llm_client):
        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))
        analyzer_service = dependencies.statement_analyzer_service
        analysis_result = analyzer_service.analyze(
            filename=sample_csv_file["filename"],
            file_content=sample_csv_file["content"],
        )

        assert analysis_result.uploaded_file_id is not None
        assert analysis_result.file_type == "CSV"
        assert analysis_result.column_mapping == {
            "date": "Data",
            "amount": "Valor",
            "description": "Descricao",
        }
        assert analysis_result.header_row_index == 1
        assert analysis_result.data_start_row_index == 3
        assert analysis_result.sample_data == [
            ["Header 1", "Header 2", "Header 3"],
            ["Data", "Valor", "Descricao"],
            ["2023-01-01", "100.00", "Deposit"],
            ["2023-01-02", "-50.00", "Withdrawal"],
            ["2023-01-03", "25.50", "Refund"],
        ]

        source = Source(name="Test Bank")
        db_session.add(source)
        db_session.flush()

        persistence_request = PersistenceRequestDTO(
            uploaded_file_id=analysis_result.uploaded_file_id,
            column_mapping=analysis_result.column_mapping,
            header_row_index=analysis_result.header_row_index,
            data_start_row_index=analysis_result.data_start_row_index,
            source_id=source.id,
        )

        persistence_service = dependencies.statement_persistence_service
        persistence_result = persistence_service.persist(persistence_request)

        assert isinstance(persistence_result, PersistenceResultDTO)
        assert persistence_result.transactions_saved == 2
        assert persistence_result.uploaded_file_id == analysis_result.uploaded_file_id

        uploaded_file_id = UUID(analysis_result.uploaded_file_id)
        uploaded_file = db_session.query(UploadedFile).filter(UploadedFile.id == uploaded_file_id).first()
        assert uploaded_file.filename == sample_csv_file["filename"]
        assert uploaded_file.content == sample_csv_file["content"]

        metadata = db_session.query(FileAnalysisMetadata).filter(FileAnalysisMetadata.uploaded_file_id == uploaded_file_id).first()
        assert metadata.uploaded_file_id == uploaded_file_id
        assert metadata.file_type == "CSV"
        assert metadata.column_mapping == {
            "date": "Data",
            "amount": "Valor",
            "description": "Descricao",
        }
        assert metadata.header_row_index == 1
        assert metadata.data_start_row_index == 3

        transactions = db_session.query(Transaction).filter(Transaction.uploaded_file_id == uploaded_file_id).all()
        assert len(transactions) == 2

        expected = [
            (date(2023, 1, 2), Decimal("-50.00"), "Withdrawal"),
            (date(2023, 1, 3), Decimal("25.50"), "Refund"),
        ]

        actual = [(t.date, t.amount, t.description) for t in transactions]
        assert Counter(actual) == Counter(expected)

    def test_analyze_duplicate_file(self, db_session, sample_csv_file, llm_client):
        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))
        analyzer_service = dependencies.statement_analyzer_service

        first_analysis = analyzer_service.analyze(
            filename=sample_csv_file["filename"],
            file_content=sample_csv_file["content"],
        )

        source = Source(name="Test Bank")
        db_session.add(source)
        db_session.flush()
        persistence_request = PersistenceRequestDTO(
            uploaded_file_id=first_analysis.uploaded_file_id,
            column_mapping=first_analysis.column_mapping,
            header_row_index=first_analysis.header_row_index,
            data_start_row_index=first_analysis.data_start_row_index,
            source_id=source.id,
        )

        persistence_service = dependencies.statement_persistence_service
        persistence_service.persist(persistence_request)

        initial_file_count = db_session.query(UploadedFile).count()
        initial_metadata_count = db_session.query(FileAnalysisMetadata).count()

        second_analysis = analyzer_service.analyze(
            filename=sample_csv_file["filename"],
            file_content=sample_csv_file["content"],
        )
        persistence_request = PersistenceRequestDTO(
            uploaded_file_id=second_analysis.uploaded_file_id,
            column_mapping=second_analysis.column_mapping,
            header_row_index=second_analysis.header_row_index,
            data_start_row_index=second_analysis.data_start_row_index,
            source_id=source.id,
        )
        persistence_service.persist(persistence_request)

        assert second_analysis.file_type == first_analysis.file_type
        assert second_analysis.column_mapping == first_analysis.column_mapping
        assert second_analysis.header_row_index == first_analysis.header_row_index
        assert second_analysis.data_start_row_index == first_analysis.data_start_row_index

        assert db_session.query(UploadedFile).count() == initial_file_count + 1
        assert db_session.query(FileAnalysisMetadata).count() == initial_metadata_count
