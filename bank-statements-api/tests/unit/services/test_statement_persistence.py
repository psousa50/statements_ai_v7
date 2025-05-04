import pytest
import pandas as pd
from unittest.mock import MagicMock
import uuid

from app.services.statement_processing.statement_persistence import StatementPersistenceService


class TestStatementPersistenceService:
    def test_persist_transactions(self):
        statement_parser = MagicMock()
        statement_parser.parse.return_value = pd.DataFrame({
            "Date": ["2023-01-01", "2023-01-02"],
            "Amount": [100.00, -200.00],
            "Description": ["Deposit", "Withdrawal"]
        })
        
        transaction_normalizer = MagicMock()
        transaction_normalizer.normalize.return_value = pd.DataFrame({
            "date": ["2023-01-01", "2023-01-02"],
            "amount": [100.00, -200.00],
            "description": ["Deposit", "Withdrawal"]
        })
        
        transaction_repo = MagicMock()
        transaction_repo.save_batch.return_value = 2
        
        persistence_service = StatementPersistenceService(
            statement_parser=statement_parser,
            transaction_normalizer=transaction_normalizer,
            transaction_repo=transaction_repo
        )
        
        file_metadata = {
            "uploaded_file_id": str(uuid.uuid4()),
            "file_type": "CSV",
            "column_mapping": {
                "date": "Date",
                "amount": "Amount",
                "description": "Description"
            },
            "header_row_index": 0,
            "data_start_row_index": 1
        }
        
        file_content = b"Date,Amount,Description\n2023-01-01,100.00,Deposit\n2023-01-02,-200.00,Withdrawal"
        
        result = persistence_service.persist(file_metadata, file_content)
        
        assert result["uploaded_file_id"] == file_metadata["uploaded_file_id"]
        assert result["transactions_saved"] == 2
        
        statement_parser.parse.assert_called_once_with(file_content, file_metadata["file_type"])
        transaction_normalizer.normalize.assert_called_once_with(
            statement_parser.parse.return_value,
            file_metadata["column_mapping"]
        )
        
        transaction_repo.save_batch.assert_called_once()
        saved_transactions = transaction_repo.save_batch.call_args[0][0]
        assert len(saved_transactions) == 2
        assert all(t["uploaded_file_id"] == file_metadata["uploaded_file_id"] for t in saved_transactions)
