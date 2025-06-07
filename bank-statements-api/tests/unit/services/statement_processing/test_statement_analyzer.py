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

        transaction_repo = MagicMock()
        transaction_repo.find_matching_transactions.return_value = []  # No duplicates in database

        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
            transaction_repo=transaction_repo,
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

        # Test new transaction statistics fields
        assert result.total_transactions == 2
        assert result.unique_transactions == 2
        assert result.duplicate_transactions == 0
        assert result.date_range == ("2023-01-01", "2023-01-02")
        assert result.total_amount == -100.0  # 100 + (-200) = -100
        assert result.total_debit == -200.0  # Only the withdrawal
        assert result.total_credit == 100.0  # Only the deposit

        file_type_detector.detect.assert_called_once_with(file_content)
        statement_parser.parse.assert_called_once_with(file_content, "CSV")
        schema_detector.detect_schema.assert_called_once()
        file_analysis_metadata_repo.find_by_hash.assert_called_once()
        uploaded_file_repo.save.assert_called_once_with(filename, file_content, "CSV")

    def test_duplicate_counting_logic(self):
        """Test that duplicate counting works correctly when multiple identical transactions exist in file"""
        file_type_detector = MagicMock()
        file_type_detector.detect.return_value = "CSV"

        statement_parser = MagicMock()
        # File contains two identical transactions
        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-01", "2023-01-02"],
                "Amount": [100.00, 100.00, -200.00],
                "Description": ["Deposit", "Deposit", "Withdrawal"],
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
        # Normalize to the same format
        transaction_normalizer.normalize.return_value = pd.DataFrame(
            {
                "date": ["2023-01-01", "2023-01-01", "2023-01-02"],
                "amount": [100.00, 100.00, -200.00],
                "description": ["Deposit", "Deposit", "Withdrawal"],
            }
        )

        uploaded_file_repo = MagicMock()
        uploaded_file_id = str(uuid.uuid4())
        uploaded_file_repo.save.return_value = UploadedFileDTO(
            id=uploaded_file_id, filename="test.csv", file_type="CSV", created_at=None
        )

        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = None

        transaction_repo = MagicMock()
        # Mock that one "Deposit" transaction already exists in database
        mock_tx = MagicMock()
        mock_tx.id = uuid.uuid4()
        transaction_repo.find_matching_transactions.return_value = [mock_tx]

        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
            transaction_repo=transaction_repo,
        )

        filename = "test.csv"
        file_content = (
            b"Date,Amount,Description\n2023-01-01,100.00,Deposit\n2023-01-01,100.00,Deposit\n2023-01-02,-200.00,Withdrawal"
        )

        result = analyzer.analyze(filename, file_content)

        # Test that duplicate counting is correct:
        # Total: 3 transactions
        # Duplicates: 1 (only one of the "Deposit" transactions is a duplicate since one exists in DB)
        # Unique: 2 (one "Deposit" is new, one "Withdrawal" is new)
        assert result.total_transactions == 3
        assert result.duplicate_transactions == 1
        assert result.unique_transactions == 2

    def test_complex_duplicate_scenario(self):
        """Test duplicate counting with a complex scenario: multiple different transactions, some duplicated"""
        file_type_detector = MagicMock()
        file_type_detector.detect.return_value = "CSV"

        statement_parser = MagicMock()
        # File contains: 2x DepositA, 3x DepositB, 1x Withdrawal
        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": [
                    "2023-01-01",
                    "2023-01-01",
                    "2023-01-02",
                    "2023-01-02",
                    "2023-01-02",
                    "2023-01-03",
                ],
                "Amount": [100.00, 100.00, 50.00, 50.00, 50.00, -200.00],
                "Description": [
                    "DepositA",
                    "DepositA",
                    "DepositB",
                    "DepositB",
                    "DepositB",
                    "Withdrawal",
                ],
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
                "date": [
                    "2023-01-01",
                    "2023-01-01",
                    "2023-01-02",
                    "2023-01-02",
                    "2023-01-02",
                    "2023-01-03",
                ],
                "amount": [100.00, 100.00, 50.00, 50.00, 50.00, -200.00],
                "description": [
                    "DepositA",
                    "DepositA",
                    "DepositB",
                    "DepositB",
                    "DepositB",
                    "Withdrawal",
                ],
            }
        )

        uploaded_file_repo = MagicMock()
        uploaded_file_id = str(uuid.uuid4())
        uploaded_file_repo.save.return_value = UploadedFileDTO(
            id=uploaded_file_id, filename="test.csv", file_type="CSV", created_at=None
        )

        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = None

        transaction_repo = MagicMock()
        # Mock that DepositA exists in database (so only one instance is a duplicate)
        # DepositB and Withdrawal don't exist (so they're all new)
        mock_tx = MagicMock()
        mock_tx.id = uuid.uuid4()

        def mock_find_matching(date, description, amount, source_id=None):
            # Only return match for DepositA
            if description == "DepositA":
                return [mock_tx]
            return []

        transaction_repo.find_matching_transactions.side_effect = mock_find_matching

        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
            transaction_repo=transaction_repo,
        )

        filename = "test.csv"
        file_content = b"Date,Amount,Description\n2023-01-01,100.00,DepositA\n2023-01-01,100.00,DepositA\n2023-01-02,50.00,DepositB\n2023-01-02,50.00,DepositB\n2023-01-02,50.00,DepositB\n2023-01-03,-200.00,Withdrawal"

        result = analyzer.analyze(filename, file_content)

        # Test that duplicate counting is correct:
        # Total: 6 transactions
        # Duplicates: 1 (only one DepositA transaction is a duplicate)
        # Unique: 5 (1x DepositA + 3x DepositB + 1x Withdrawal are new)
        assert result.total_transactions == 6
        assert result.duplicate_transactions == 1
        assert result.unique_transactions == 5

    def test_real_world_duplicate_scenario(self):
        """Test the exact scenario user is experiencing: 1 transaction in DB, file with 2 identical transactions"""
        file_type_detector = MagicMock()
        file_type_detector.detect.return_value = "CSV"

        statement_parser = MagicMock()
        # File contains two identical transactions that match one in database
        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-01"],
                "Amount": [100.50, 100.50],
                "Description": ["Coffee Shop", "Coffee Shop"],
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
        # Return the normalized data as strings (as would happen in real processing)
        transaction_normalizer.normalize.return_value = pd.DataFrame(
            {
                "date": ["2023-01-01", "2023-01-01"],  # String dates
                "amount": [100.50, 100.50],  # Float amounts
                "description": ["Coffee Shop", "Coffee Shop"],
            }
        )

        uploaded_file_repo = MagicMock()
        uploaded_file_id = str(uuid.uuid4())
        uploaded_file_repo.save.return_value = UploadedFileDTO(
            id=uploaded_file_id, filename="test.csv", file_type="CSV", created_at=None
        )

        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = None

        transaction_repo = MagicMock()
        # Mock that one "Coffee Shop" transaction already exists in database
        mock_tx = MagicMock()
        mock_tx.id = uuid.uuid4()
        transaction_repo.find_matching_transactions.return_value = [mock_tx]

        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
            transaction_repo=transaction_repo,
        )

        filename = "test.csv"
        file_content = b"Date,Amount,Description\n2023-01-01,100.50,Coffee Shop\n2023-01-01,100.50,Coffee Shop"

        result = analyzer.analyze(filename, file_content)

        # Verify that the transaction repository method was called correctly
        transaction_repo.find_matching_transactions.assert_called()

        # Check that it was called twice (once for each transaction in the file)
        assert transaction_repo.find_matching_transactions.call_count == 2

        # Test that duplicate counting is correct:
        # Total: 2 transactions in file
        # Duplicates: 1 (only one of the identical transactions should be marked as duplicate)
        # Unique: 1 (the other identical transaction is new)
        assert result.total_transactions == 2
        assert result.duplicate_transactions == 1
        assert result.unique_transactions == 1

    def test_user_reported_issue_scenario(self):
        """Test the exact user scenario: 1 tx in DB, file with 2 identical txs should detect 1 duplicate"""
        file_type_detector = MagicMock()
        file_type_detector.detect.return_value = "CSV"

        statement_parser = MagicMock()
        # File contains two identical transactions X
        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-01"],
                "Amount": [50.00, 50.00],
                "Description": ["Transaction X", "Transaction X"],
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
                "date": ["2023-01-01", "2023-01-01"],
                "amount": [50.00, 50.00],
                "description": ["Transaction X", "Transaction X"],
            }
        )

        uploaded_file_repo = MagicMock()
        uploaded_file_id = str(uuid.uuid4())
        uploaded_file_repo.save.return_value = UploadedFileDTO(
            id=uploaded_file_id, filename="test.csv", file_type="CSV", created_at=None
        )

        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = None

        transaction_repo = MagicMock()
        # Mock that transaction X exists once in database
        mock_tx = MagicMock()
        mock_tx.id = uuid.uuid4()
        transaction_repo.find_matching_transactions.return_value = [mock_tx]

        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
            transaction_repo=transaction_repo,
        )

        filename = "test.csv"
        file_content = b"Date,Amount,Description\n2023-01-01,50.00,Transaction X\n2023-01-01,50.00,Transaction X"

        result = analyzer.analyze(filename, file_content)

        # Scenario: 1 tx X in DB, file with 2 identical txs X
        # Expected: 1 duplicate (since DB has 1 and min(2 file count, 1 db count) = 1)
        assert result.total_transactions == 2
        assert result.duplicate_transactions == 1  # This should detect 1 duplicate
        assert result.unique_transactions == 1

    def test_exact_user_scenario_step_by_step(self):
        """Test the exact user scenario step by step: empty DB -> upload 1 tx -> upload same file -> upload file with 2 identical txs"""
        file_type_detector = MagicMock()
        file_type_detector.detect.return_value = "CSV"

        statement_parser = MagicMock()
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
        uploaded_file_repo = MagicMock()
        file_analysis_metadata_repo = MagicMock()
        file_analysis_metadata_repo.find_by_hash.return_value = None
        transaction_repo = MagicMock()

        analyzer = StatementAnalyzerService(
            file_type_detector=file_type_detector,
            statement_parser=statement_parser,
            schema_detector=schema_detector,
            transaction_normalizer=transaction_normalizer,
            uploaded_file_repo=uploaded_file_repo,
            file_analysis_metadata_repo=file_analysis_metadata_repo,
            transaction_repo=transaction_repo,
        )

        # Step 1: Empty DB - upload file with 1 transaction
        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01"],
                "Amount": [50.00],
                "Description": ["Coffee Shop"],
            }
        )
        transaction_normalizer.normalize.return_value = pd.DataFrame(
            {
                "date": ["2023-01-01"],
                "amount": [50.00],
                "description": ["Coffee Shop"],
            }
        )
        uploaded_file_repo.save.return_value = UploadedFileDTO(
            id=str(uuid.uuid4()), filename="test1.csv", file_type="CSV", created_at=None
        )
        transaction_repo.find_matching_transactions.return_value = []  # Empty DB

        result1 = analyzer.analyze("test1.csv", b"Date,Amount,Description\n2023-01-01,50.00,Coffee Shop")

        assert result1.total_transactions == 1
        assert result1.duplicate_transactions == 0
        assert result1.unique_transactions == 1

        # Step 2: DB now has 1 transaction - upload same file again
        # Mock that the transaction now exists in DB
        mock_tx = MagicMock()
        mock_tx.id = uuid.uuid4()
        transaction_repo.find_matching_transactions.return_value = [mock_tx]

        result2 = analyzer.analyze("test1.csv", b"Date,Amount,Description\n2023-01-01,50.00,Coffee Shop")

        assert result2.total_transactions == 1
        assert result2.duplicate_transactions == 1  # Should detect 1 duplicate
        assert result2.unique_transactions == 0

        # Step 3: Upload file with 2 identical transactions (same as in DB)
        statement_parser.parse.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-01"],
                "Amount": [50.00, 50.00],
                "Description": ["Coffee Shop", "Coffee Shop"],
            }
        )
        transaction_normalizer.normalize.return_value = pd.DataFrame(
            {
                "date": ["2023-01-01", "2023-01-01"],
                "amount": [50.00, 50.00],
                "description": ["Coffee Shop", "Coffee Shop"],
            }
        )
        # DB still has same 1 transaction
        transaction_repo.find_matching_transactions.return_value = [mock_tx]

        result3 = analyzer.analyze(
            "test2.csv",
            b"Date,Amount,Description\n2023-01-01,50.00,Coffee Shop\n2023-01-01,50.00,Coffee Shop",
        )

        # This should detect 1 duplicate: min(2 file_count, 1 db_count) = 1
        assert result3.total_transactions == 2
        assert result3.duplicate_transactions == 1  # This is the failing case
        assert result3.unique_transactions == 1
