import uuid
from unittest.mock import MagicMock, Mock

import pandas as pd

from app.domain.dto.statement_processing import PersistenceResultDTO, TransactionDTO
from app.domain.dto.uploaded_file import FileAnalysisMetadataDTO, UploadedFileDTO
from app.services.statement_processing.statement_persistence import StatementPersistenceService


class TestStatementPersistenceService:
    def test_save_processed_transactions(self):
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
        transaction_repo.save_batch.return_value = (
            2,
            0,
        )  # (transactions_saved, duplicated_transactions)

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
            account_id=None,
            column_mapping={},
            header_row_index=0,
            data_start_row_index=1,
            created_at=None,
        )

        statement_repo = Mock()
        mock_statement = Mock()
        mock_statement.id = uuid.uuid4()
        statement_repo.save.return_value = mock_statement

        persistence_service = StatementPersistenceService(
            statement_parser=statement_parser,
            transaction_normalizer=transaction_normalizer,
            transaction_repo=transaction_repo,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
            statement_repo=statement_repo,
        )

        uploaded_file_id = str(uuid.uuid4())
        account_id = uuid.uuid4()

        # Create processed transaction DTOs
        processed_dtos = [
            TransactionDTO(
                date="2023-01-01",
                amount=100.00,
                description="Deposit",
                account_id=str(account_id),
                row_index=0,
                sort_index=0,
                source_type="UPLOAD",
            ),
            TransactionDTO(
                date="2023-01-02",
                amount=-200.00,
                description="Withdrawal",
                account_id=str(account_id),
                row_index=1,
                sort_index=1,
                source_type="UPLOAD",
            ),
        ]

        result = persistence_service.save_processed_transactions(
            processed_dtos=processed_dtos, account_id=account_id, uploaded_file_id=uploaded_file_id
        )

        assert isinstance(result, PersistenceResultDTO)
        assert result.uploaded_file_id == uploaded_file_id
        assert result.transactions_saved == 2
        assert result.duplicated_transactions == 0

        uploaded_file_repo.find_by_id.assert_called_once_with(uploaded_file_id)

        transaction_repo.save_batch.assert_called_once()
        saved_transactions = transaction_repo.save_batch.call_args[0][0]
        assert len(saved_transactions) == 2
        assert all(isinstance(t, TransactionDTO) for t in saved_transactions)
        assert all(t.statement_id == str(mock_statement.id) for t in saved_transactions)
