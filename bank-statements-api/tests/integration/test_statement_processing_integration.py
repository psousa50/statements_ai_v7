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
from app.domain.dto.statement_processing import PersistenceResultDTO, TransactionDTO
from app.domain.models.account import Account
from app.domain.models.statement import Statement
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
    llm_client = MagicMock()
    llm_client.generate.return_value = """
    {
        "column_mapping": {
            "date": "Data",
            "amount": "Valor",
            "description": "Descricao"
        },
        "header_row_index": 1,
        "data_start_row_index": 3
    }
    """
    return llm_client


@pytest.mark.integration
class TestStatementProcessingIntegration:
    def test_analyze_and_persist_new_file(self, db_session, llm_client):
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

        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))
        analyzer_service = dependencies.statement_analyzer_service
        analysis_result = analyzer_service.analyze(
            filename=filename,
            file_content=content,
        )

        assert analysis_result.uploaded_file_id is not None
        assert analysis_result.file_type == "CSV"
        assert analysis_result.column_mapping == {
            "date": "Data",
            "amount": "Valor",
            "description": "Descricao",
        }
        assert analysis_result.header_row_index == 1
        assert analysis_result.data_start_row_index == 2
        assert analysis_result.sample_data == [
            ["Header 1", "Header 2", "Header 3"],
            ["Data", "Valor", "Descricao"],
            ["2023-01-01", "100.00", "Deposit"],
            ["2023-01-02", "-50.00", "Withdrawal"],
            ["2023-01-03", "25.50", "Refund"],
        ]

        source = Account(name="Test Bank")
        db_session.add(source)
        db_session.flush()

        # Create transaction DTOs manually for testing
        from app.domain.models.transaction import SourceType

        processed_dtos = [
            TransactionDTO(
                date="2023-01-01",
                amount=100.00,
                description="Deposit",
                account_id=str(source.id),
                row_index=0,
                sort_index=0,
                source_type=SourceType.UPLOAD.value,
            ),
            TransactionDTO(
                date="2023-01-02",
                amount=-50.00,
                description="Withdrawal",
                account_id=str(source.id),
                row_index=1,
                sort_index=1,
                source_type=SourceType.UPLOAD.value,
            ),
            TransactionDTO(
                date="2023-01-03",
                amount=25.50,
                description="Refund",
                account_id=str(source.id),
                row_index=2,
                sort_index=2,
                source_type=SourceType.UPLOAD.value,
            ),
        ]

        persistence_service = dependencies.statement_persistence_service
        persistence_result = persistence_service.save_processed_transactions(
            processed_dtos=processed_dtos, account_id=source.id, uploaded_file_id=analysis_result.uploaded_file_id
        )

        assert isinstance(persistence_result, PersistenceResultDTO)
        assert persistence_result.transactions_saved == 3
        assert persistence_result.uploaded_file_id == analysis_result.uploaded_file_id

        uploaded_file_id = UUID(analysis_result.uploaded_file_id)
        uploaded_file = db_session.query(UploadedFile).filter(UploadedFile.id == uploaded_file_id).first()
        assert uploaded_file.filename == filename
        assert uploaded_file.content == content

        # Note: File analysis metadata is now handled separately in the production flow

        # Get the statement that was created
        statement = db_session.query(Statement).filter(Statement.account_id == source.id).first()
        assert statement is not None
        assert statement.filename == filename
        assert statement.content == content

        transactions = db_session.query(Transaction).filter(Transaction.statement_id == statement.id).all()
        assert len(transactions) == 3

        expected = [
            (date(2023, 1, 2), Decimal("-50.00"), "Withdrawal"),
            (date(2023, 1, 3), Decimal("25.50"), "Refund"),
            (date(2023, 1, 1), Decimal("100.00"), "Deposit"),
        ]

        actual = [(t.date, t.amount, t.description) for t in transactions]
        assert Counter(actual) == Counter(expected)

    def test_analyze_duplicate_file(self, db_session, llm_client):
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
        dependencies = build_internal_dependencies(ExternalDependencies(db=db_session, llm_client=llm_client))
        analyzer_service = dependencies.statement_analyzer_service

        first_analysis = analyzer_service.analyze(
            filename=filename,
            file_content=content,
        )

        source = Account(name="Test Bank")
        db_session.add(source)
        db_session.flush()
        # Create transaction DTOs for first upload
        from app.domain.models.transaction import SourceType

        first_processed_dtos = [
            TransactionDTO(
                date="2023-01-01",
                amount=100.00,
                description="Deposit",
                account_id=str(source.id),
                row_index=0,
                sort_index=0,
                source_type=SourceType.UPLOAD.value,
            ),
            TransactionDTO(
                date="2023-01-02",
                amount=-50.00,
                description="Withdrawal",
                account_id=str(source.id),
                row_index=1,
                sort_index=1,
                source_type=SourceType.UPLOAD.value,
            ),
            TransactionDTO(
                date="2023-01-03",
                amount=25.50,
                description="Refund",
                account_id=str(source.id),
                row_index=2,
                sort_index=2,
                source_type=SourceType.UPLOAD.value,
            ),
        ]

        persistence_service = dependencies.statement_persistence_service
        persistence_service.save_processed_transactions(
            processed_dtos=first_processed_dtos, account_id=source.id, uploaded_file_id=first_analysis.uploaded_file_id
        )

        initial_file_count = db_session.query(UploadedFile).count()

        second_analysis = analyzer_service.analyze(
            filename=filename,
            file_content=content,
        )
        # Create transaction DTOs for second upload
        second_processed_dtos = [
            TransactionDTO(
                date="2023-01-01",
                amount=100.00,
                description="Deposit",
                account_id=str(source.id),
                row_index=0,
                sort_index=0,
                source_type=SourceType.UPLOAD.value,
            ),
            TransactionDTO(
                date="2023-01-02",
                amount=-50.00,
                description="Withdrawal",
                account_id=str(source.id),
                row_index=1,
                sort_index=1,
                source_type=SourceType.UPLOAD.value,
            ),
            TransactionDTO(
                date="2023-01-03",
                amount=25.50,
                description="Refund",
                account_id=str(source.id),
                row_index=2,
                sort_index=2,
                source_type=SourceType.UPLOAD.value,
            ),
        ]
        persistence_service.save_processed_transactions(
            processed_dtos=second_processed_dtos, account_id=source.id, uploaded_file_id=second_analysis.uploaded_file_id
        )

        assert second_analysis.file_type == first_analysis.file_type
        assert second_analysis.column_mapping == first_analysis.column_mapping
        assert second_analysis.header_row_index == first_analysis.header_row_index
        assert second_analysis.data_start_row_index == first_analysis.data_start_row_index

        assert db_session.query(UploadedFile).count() == initial_file_count + 1
