import uuid
from unittest.mock import MagicMock

import pandas as pd

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
        uploaded_file_repo.find_by_id.return_value = {
            "id": str(uuid.uuid4()),
            "filename": "test.csv",
            "content": b"Date,Amount,Description\n2023-01-01,100.00,Deposit\n2023-01-02,-200.00,Withdrawal",
        }

        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.save.return_value = {"id": str(uuid.uuid4())}

        persistence_service = StatementPersistenceService(
            statement_parser=statement_parser,
            transaction_normalizer=transaction_normalizer,
            transaction_repo=transaction_repo,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
        )

        analysis_result = {
            "uploaded_file_id": str(uuid.uuid4()),
            "file_type": "CSV",
            "column_mapping": {
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            "header_row_index": 0,
            "data_start_row_index": 1,
            "sample_data": [
                {"date": "2023-01-01", "amount": 100.00, "description": "Deposit"},
                {"date": "2023-01-02", "amount": -200.00, "description": "Withdrawal"},
            ],
            "file_hash": "abc123",
        }

        result = persistence_service.persist(analysis_result)

        assert result["uploaded_file_id"] == analysis_result["uploaded_file_id"]
        assert result["transactions_saved"] == 2

        uploaded_file_repo.find_by_id.assert_called_once_with(analysis_result["uploaded_file_id"])
        statement_parser.parse.assert_called_once()
        transaction_normalizer.normalize.assert_called_once_with(statement_parser.parse.return_value, analysis_result["column_mapping"])

        transaction_repo.save_batch.assert_called_once()
        saved_transactions = transaction_repo.save_batch.call_args[0][0]
        assert len(saved_transactions) == 2
        assert all(t["uploaded_file_id"] == analysis_result["uploaded_file_id"] for t in saved_transactions)

        file_analysis_metadata_repo.save.assert_called_once_with(
            uploaded_file_id=analysis_result["uploaded_file_id"],
            file_hash=analysis_result["file_hash"],
            file_type=analysis_result["file_type"],
            column_mapping=analysis_result["column_mapping"],
            header_row_index=analysis_result["header_row_index"],
            data_start_row_index=analysis_result["data_start_row_index"],
        )
