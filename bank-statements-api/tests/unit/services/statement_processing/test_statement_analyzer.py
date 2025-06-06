import uuid
from unittest.mock import MagicMock

import pandas as pd

from app.domain.dto.statement_processing import AnalysisResultDTO
from app.domain.dto.uploaded_file import UploadedFileDTO
from app.services.schema_detection.llm_schema_detector import ConversionModel
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService


class TestStatementAnalyzerService:
    def test_analyze_new_file(self):
        file_type_detector = MagicMock()
        file_type_detector.detect.return_value = "CSV"

        statement_parser = MagicMock()
        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "Amount": [100.00, -200.00],
                "Description": ["Deposit", "Withdrawal"],
            }
        )

        schema_detector = MagicMock()
        schema_detector.detect_schema.return_value = ConversionModel(
            column_map={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row=0,
            start_row=1,
        )

        transaction_normalizer = MagicMock()
        transaction_normalizer.normalize.return_value = pd.DataFrame(
            {
                "date": ["2023-01-01", "2023-01-02"],
                "amount": [100.00, -200.00],
                "description": ["Deposit", "Withdrawal"],
            }
        )

        uploaded_file_repo = MagicMock()
        uploaded_file_id = str(uuid.uuid4())
        uploaded_file_repo.save.return_value = UploadedFileDTO(
            id=uploaded_file_id, filename="test.csv", file_type="CSV", created_at=None
        )

        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = None

        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
        )

        filename = "test.csv"
        file_content = b"Date,Amount,Description\n2023-01-01,100.00,Deposit\n2023-01-02,-200.00,Withdrawal"

        result = analyzer.analyze(filename, file_content)

        assert isinstance(result, AnalysisResultDTO)
        assert result.uploaded_file_id == uploaded_file_id
        assert result.file_type == "CSV"
        assert result.column_mapping == {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }
        assert result.header_row_index == 0
        assert result.data_start_row_index == 1
        assert result.sample_data is not None

        file_type_detector.detect.assert_called_once_with(file_content)
        statement_parser.parse.assert_called_once_with(file_content, "CSV")
        schema_detector.detect_schema.assert_called_once()
        file_analysis_metadata_repo.find_by_hash.assert_called_once()
        uploaded_file_repo.save.assert_called_once_with(filename, file_content, "CSV")
