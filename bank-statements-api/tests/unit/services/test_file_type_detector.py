import pytest
from unittest.mock import MagicMock

# Import the class we're testing
# This will fail until we create the actual implementation
from app.services.statement_processing.file_type_detector import StatementFileTypeDetector


class TestStatementFileTypeDetector:
    def test_detect_csv_file(self):
        # Arrange
        detector = StatementFileTypeDetector()
        file_content = b"date,amount,description\n2023-01-01,100.00,Test transaction"
        
        # Act
        file_type = detector.detect(file_content)
        
        # Assert
        assert file_type == "CSV"
    
    def test_detect_xlsx_file(self):
        # Arrange
        detector = StatementFileTypeDetector()
        # XLSX files have a specific binary signature
        # This is a simplified mock of an XLSX file header
        file_content = b"PK\x03\x04" + b"\x00" * 100
        
        # Act
        file_type = detector.detect(file_content)
        
        # Assert
        assert file_type == "XLSX"
    
    def test_unknown_file_type(self):
        # Arrange
        detector = StatementFileTypeDetector()
        file_content = b"This is not a CSV or XLSX file"
        
        # Act
        file_type = detector.detect(file_content)
        
        # Assert
        assert file_type == "UNKNOWN"
