import pytest
import pandas as pd
from unittest.mock import MagicMock
import uuid
import hashlib

from app.services.statement_processing.statement_analyzer import StatementAnalyzerService


class TestStatementAnalyzerService:
    def test_analyze_new_file(self):
        file_type_detector = MagicMock()
        file_type_detector.detect.return_value = "CSV"
        
        statement_parser = MagicMock()
        statement_parser.parse.return_value = pd.DataFrame({
            "Date": ["2023-01-01", "2023-01-02"],
            "Amount": [100.00, -200.00],
            "Description": ["Deposit", "Withdrawal"]
        })
        
        schema_detector = MagicMock()
        schema_detector.detect_schema.return_value = {
            "column_mapping": {
                "date": "Date",
                "amount": "Amount",
                "description": "Description"
            },
            "header_row_index": 0,
            "data_start_row_index": 1
        }
        
        transaction_normalizer = MagicMock()
        transaction_normalizer.normalize.return_value = pd.DataFrame({
            "date": ["2023-01-01", "2023-01-02"],
            "amount": [100.00, -200.00],
            "description": ["Deposit", "Withdrawal"]
        })
        
        uploaded_file_repo = MagicMock()
        uploaded_file_id = str(uuid.uuid4())
        uploaded_file_repo.save.return_value = {"id": uploaded_file_id}
        
        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = None
        
        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo
        )
        
        filename = "test.csv"
        file_content = b"Date,Amount,Description\n2023-01-01,100.00,Deposit\n2023-01-02,-200.00,Withdrawal"
        
        result = analyzer.analyze(filename, file_content)
        
        assert "uploaded_file_id" in result
        assert result["uploaded_file_id"] == uploaded_file_id
        assert result["file_type"] == "CSV"
        assert result["column_mapping"] == {
            "date": "Date",
            "amount": "Amount",
            "description": "Description"
        }
        assert result["header_row_index"] == 0
        assert result["data_start_row_index"] == 1
        assert "sample_data" in result
        assert "file_hash" in result
        
        file_type_detector.detect.assert_called_once_with(file_content)
        statement_parser.parse.assert_called_once_with(file_content, "CSV")
        schema_detector.detect_schema.assert_called_once()
        transaction_normalizer.normalize.assert_called_once()
        file_analysis_metadata_repo.find_by_hash.assert_called_once()
        uploaded_file_repo.save.assert_called_once_with(filename, file_content)
    
    def test_analyze_duplicate_file(self):
        file_type_detector = MagicMock()
        statement_parser = MagicMock()
        schema_detector = MagicMock()
        transaction_normalizer = MagicMock()
        uploaded_file_repo = MagicMock()
        
        filename = "test.csv"
        file_content = b"Date,Amount,Description\n2023-01-01,100.00,Deposit\n2023-01-02,-200.00,Withdrawal"
        
        # Calculate the actual hash that would be generated
        hasher = hashlib.sha256()
        hasher.update(filename.encode())
        hasher.update(file_content)
        file_hash = hasher.hexdigest()
        
        uploaded_file_id = str(uuid.uuid4())
        existing_metadata = {
            "id": str(uuid.uuid4()),
            "uploaded_file_id": uploaded_file_id,
            "file_type": "CSV",
            "column_mapping": {
                "date": "Date",
                "amount": "Amount",
                "description": "Description"
            },
            "header_row_index": 0,
            "data_start_row_index": 1,
            "normalized_sample": [
                {"date": "2023-01-01", "amount": 100.00, "description": "Deposit"},
                {"date": "2023-01-02", "amount": -200.00, "description": "Withdrawal"}
            ],
            "file_hash": file_hash
        }
        
        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = existing_metadata
        
        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo
        )
        
        result = analyzer.analyze(filename, file_content)
        
        assert result["uploaded_file_id"] == uploaded_file_id
        assert result["file_type"] == existing_metadata["file_type"]
        assert result["column_mapping"] == existing_metadata["column_mapping"]
        assert result["header_row_index"] == existing_metadata["header_row_index"]
        assert result["data_start_row_index"] == existing_metadata["data_start_row_index"]
        assert result["sample_data"] == existing_metadata["normalized_sample"]
        assert result["file_hash"] == existing_metadata["file_hash"]
        
        file_type_detector.detect.assert_not_called()
        statement_parser.parse.assert_not_called()
        schema_detector.detect_schema.assert_not_called()
        transaction_normalizer.normalize.assert_not_called()
        uploaded_file_repo.save.assert_not_called()
        file_analysis_metadata_repo.find_by_hash.assert_called_once()
