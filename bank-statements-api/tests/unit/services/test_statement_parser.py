import pytest
import pandas as pd
import io

from app.services.statement_processing.statement_parser import StatementParser


class TestStatementParser:
    def test_parse_csv_file(self):
        parser = StatementParser()
        file_content = b"date,amount,description\n2023-01-01,100.00,Test transaction"
        file_type = "CSV"
        
        df = parser.parse(file_content, file_type)
        
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (1, 3)
        assert list(df.columns) == ["date", "amount", "description"]
        assert df.iloc[0]["date"] == "2023-01-01"
        assert df.iloc[0]["amount"] == 100.00
        assert df.iloc[0]["description"] == "Test transaction"
    
    def test_parse_xlsx_file(self):
        parser = StatementParser()
        
        sample_df = pd.DataFrame({
            "date": ["2023-01-01", "2023-01-02"],
            "amount": [100.00, 200.00],
            "description": ["Test 1", "Test 2"]
        })
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            sample_df.to_excel(writer, index=False)
        
        file_content = buffer.getvalue()
        file_type = "XLSX"
        
        df = parser.parse(file_content, file_type)
        
        assert isinstance(df, pd.DataFrame)
        assert "date" in df.columns
        assert "amount" in df.columns
        assert "description" in df.columns
        assert len(df) == 2
    
    def test_unsupported_file_type(self):
        parser = StatementParser()
        file_content = b"some content"
        file_type = "UNKNOWN"
        
        with pytest.raises(ValueError, match="Unsupported file type: UNKNOWN"):
            parser.parse(file_content, file_type)
