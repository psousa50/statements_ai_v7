"""
Integration tests for statement upload that test the actual service implementation
without excessive mocking to catch import errors and other runtime issues.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from app.api.schemas import StatementUploadRequest
from app.domain.dto.statement_processing import TransactionDTO
from app.services.statement_processing.statement_upload import StatementUploadService


class TestStatementUploadIntegration:
    """Integration tests that use real service implementations to catch runtime errors."""

    def test_upload_service_with_real_dto_processing(self):
        """Test that DTO processing actually works with real implementations."""

        # Create real service with minimal mocking
        statement_parser = MagicMock()
        transaction_normalizer = MagicMock()
        uploaded_file_repo = MagicMock()
        file_analysis_metadata_repo = MagicMock()
        transaction_processing_orchestrator = MagicMock()
        statement_persistence_service = MagicMock()

        # Mock file and parsing
        uploaded_file = MagicMock()
        uploaded_file.content = b"test,content"
        uploaded_file.file_type = "CSV"
        uploaded_file_repo.find_by_id.return_value = uploaded_file

        # Mock dataframe processing
        import pandas as pd

        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01"],
                "Amount": [100.0],
                "Description": ["Test Transaction"],
            }
        )

        normalized_df = pd.DataFrame(
            {
                "date": ["2023-01-01"],
                "amount": [100.0],
                "description": ["Test Transaction"],
            }
        )
        transaction_normalizer.normalize.return_value = normalized_df

        # Create service instance
        service = StatementUploadService(
            statement_parser=statement_parser,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
            transaction_processing_orchestrator=transaction_processing_orchestrator,
            statement_persistence_service=statement_persistence_service,
        )

        # Test DTO parsing (this should work without import errors)
        request = StatementUploadRequest(
            uploaded_file_id=str(uuid4()),
            source_id=str(uuid4()),
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
        )

        # This would catch the import error if it existed
        dtos = service._parse_to_transaction_dtos(
            uploaded_file_id=request.uploaded_file_id,
            column_mapping=request.column_mapping,
            header_row_index=request.header_row_index,
            data_start_row_index=request.data_start_row_index,
            source_id=request.source_id,
        )

        # Verify DTOs were created correctly
        assert len(dtos) == 1
        assert isinstance(dtos[0], TransactionDTO)
        assert dtos[0].description == "Test Transaction"
        assert dtos[0].amount == 100.0

    def test_orchestrator_dto_processing_with_real_implementation(self):
        """Test that the orchestrator's DTO processing method works without import errors."""

        from app.domain.dto.statement_processing import TransactionDTO
        from app.services.transaction_processing_orchestrator import (
            TransactionProcessingOrchestrator,
        )

        # Create real orchestrator with mocked dependencies
        rule_based_service = MagicMock()
        background_job_service = MagicMock()
        transaction_repository = MagicMock()

        # Mock rule-based categorization (empty results)
        rule_based_service.categorize_batch.return_value = {}

        orchestrator = TransactionProcessingOrchestrator(
            rule_based_categorization_service=rule_based_service,
            background_job_service=background_job_service,
            transaction_repository=transaction_repository,
        )

        # Create test DTOs
        test_dtos = [
            TransactionDTO(
                date="2023-01-01",
                amount=100.0,
                description="Test Transaction 1",
                uploaded_file_id=str(uuid4()),
                source_id=str(uuid4()),
            ),
            TransactionDTO(
                date="2023-01-02",
                amount=200.0,
                description="Test Transaction 2",
                uploaded_file_id=str(uuid4()),
                source_id=str(uuid4()),
            ),
        ]

        # This would fail with import error if normalize_description import was wrong
        result = orchestrator.process_transaction_dtos(
            transaction_dtos=test_dtos,
            uploaded_file_id=uuid4(),
        )

        # Verify processing completed
        assert result.total_processed == 2
        assert result.rule_based_matches == 0  # No rules matched
        assert result.unmatched_dto_count == 2
        assert len(result.processed_dtos) == 2

        # Verify DTOs have normalized descriptions
        for dto in result.processed_dtos:
            assert dto.normalized_description is not None
            assert isinstance(dto.normalized_description, str)
