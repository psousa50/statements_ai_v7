import uuid
from unittest.mock import ANY, MagicMock

import pandas as pd

from app.domain.dto.statement_processing import PersistenceRequestDTO, PersistenceResultDTO, TransactionDTO
from app.domain.dto.uploaded_file import FileAnalysisMetadataDTO, UploadedFileDTO
from app.services.statement_processing.statement_persistence import StatementPersistenceService


class TestStatementPersistenceService:
    def test_persist_transactions(self):
        statement_parser = MagicMock()
        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "Amount": [100.00, -200.00],
                "Description": ["Deposit", "Withdrawal"],
            }
        )

        transaction_normalizer = MagicMock()
        transaction_normalizer.normalize.return_value = pd.DataFrame(
            {
                "date": ["2023-01-01", "2023-01-02"],
                "amount": [100.00, -200.00],
                "description": ["Deposit", "Withdrawal"],
            }
        )

        transaction_repo = MagicMock()
        transaction_repo.save_batch.return_value = 2

        uploaded_file_repo = MagicMock()
        uploaded_file_repo.find_by_id.return_value = UploadedFileDTO(
            id=str(uuid.uuid4()),
            filename="test.csv",
            file_type="CSV",
            content=b"Date,Amount,Description\n2023-01-01,100.00,Deposit\n2023-01-02,-200.00,Withdrawal",
            created_at=None,
        )

        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = None
        file_analysis_metadata_repo.save.return_value = FileAnalysisMetadataDTO(
            id=str(uuid.uuid4()),
            file_hash="abc123",
            source_id=None,
            column_mapping={},
            header_row_index=0,
            data_start_row_index=1,
            created_at=None,
        )

        persistence_service = StatementPersistenceService(
            statement_parser=statement_parser,
            transaction_normalizer=transaction_normalizer,
            transaction_repo=transaction_repo,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
        )

        uploaded_file_id = str(uuid.uuid4())
        source_id = uuid.uuid4()

        persistence_request = PersistenceRequestDTO(
            source_id=source_id,
            uploaded_file_id=uploaded_file_id,
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
        )

        result = persistence_service.persist(persistence_request)

        assert isinstance(result, PersistenceResultDTO)
        assert result.uploaded_file_id == uploaded_file_id
        assert result.transactions_saved == 2

        uploaded_file_repo.find_by_id.assert_called_once_with(uploaded_file_id)
        statement_parser.parse.assert_called_once()
        transaction_normalizer.normalize.assert_called_once_with(ANY, persistence_request.column_mapping)

        transaction_repo.save_batch.assert_called_once()
        saved_transactions = transaction_repo.save_batch.call_args[0][0]
        assert len(saved_transactions) == 2
        assert all(isinstance(t, TransactionDTO) for t in saved_transactions)
        assert all(t.uploaded_file_id == uploaded_file_id for t in saved_transactions)

        file_analysis_metadata_repo.save.assert_called_once_with(
            file_hash=ANY,
            column_mapping=persistence_request.column_mapping,
            header_row_index=persistence_request.header_row_index,
            data_start_row_index=persistence_request.data_start_row_index,
            source_id=source_id,
        )
