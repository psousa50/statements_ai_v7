from app.services.statement_processing.file_type_detector import StatementFileTypeDetector


class TestStatementFileTypeDetector:
    def test_detect_csv_file(self):
        detector = StatementFileTypeDetector()
        file_content = b"date,amount,description\n2023-01-01,100.00,Test transaction"
        file_type = detector.detect(file_content)
        assert file_type == "CSV"

    def test_detect_tsv_file(self):
        detector = StatementFileTypeDetector()
        file_content = b"date\tamount\tdescription\n2023-01-01\t100.00\tTest transaction"
        file_type = detector.detect(file_content)
        assert file_type == "TSV"

    def test_detect_tsv_file_with_commas_in_data(self):
        detector = StatementFileTypeDetector()
        file_content = b"date\tamount\tdescription\n2023-01-01\t1,234.56\tShop, Lisbon"
        file_type = detector.detect(file_content)
        assert file_type == "TSV"

    def test_detect_tsv_file_with_cp1252_encoding(self):
        detector = StatementFileTypeDetector()
        file_content = "Data\tDescrição\tMontante\n2024-01-01\tConta à ordem\t19,80".encode("cp1252")
        file_type = detector.detect(file_content)
        assert file_type == "TSV"

    def test_detect_xlsx_file(self):
        detector = StatementFileTypeDetector()
        file_content = b"PK\x03\x04" + b"\x00" * 100
        file_type = detector.detect(file_content)
        assert file_type == "XLSX"

    def test_unknown_file_type(self):
        detector = StatementFileTypeDetector()
        file_content = b"This is not a CSV or XLSX file"
        file_type = detector.detect(file_content)
        assert file_type == "UNKNOWN"
