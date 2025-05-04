import pytest
import pandas as pd
from unittest.mock import MagicMock

from app.services.statement_processing.schema_detector import SchemaDetector, LLMClient


class MockLLMClient(LLMClient):
    def __init__(self, fixed_response: str):
        self.fixed_response = fixed_response
        self.last_prompt = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.fixed_response


class TestSchemaDetector:
    def test_detect_schema_with_llm(self):
        llm_response = """
        {
            "column_mapping": {
                "date": "Date",
                "amount": "Amount",
                "description": "Description"
            },
            "header_row_index": 0,
            "data_start_row_index": 1
        }
        """
        llm_client = MockLLMClient(llm_response)
        detector = SchemaDetector(llm_client)
        
        df = pd.DataFrame({
            "Date": ["2023-01-01", "2023-01-02"],
            "Amount": [100.00, 200.00],
            "Description": ["Test 1", "Test 2"]
        })
        
        result = detector.detect_schema(df)
        
        assert result["column_mapping"] == {
            "date": "Date",
            "amount": "Amount",
            "description": "Description"
        }
        assert result["header_row_index"] == 0
        assert result["data_start_row_index"] == 1
        assert llm_client.last_prompt is not None
        
    def test_detect_schema_with_complex_mapping(self):
        llm_response = """
        {
            "column_mapping": {
                "date": "Transaction Date",
                "amount": "Value (EUR)",
                "description": "Transaction Details"
            },
            "header_row_index": 2,
            "data_start_row_index": 3
        }
        """
        llm_client = MockLLMClient(llm_response)
        detector = SchemaDetector(llm_client)
        
        df = pd.DataFrame({
            "Transaction Date": ["2023-01-01", "2023-01-02"],
            "Value (EUR)": [100.00, 200.00],
            "Transaction Details": ["Test 1", "Test 2"]
        })
        
        result = detector.detect_schema(df)
        
        assert result["column_mapping"] == {
            "date": "Transaction Date",
            "amount": "Value (EUR)",
            "description": "Transaction Details"
        }
        assert result["header_row_index"] == 2
        assert result["data_start_row_index"] == 3
        
    def test_invalid_llm_response(self):
        llm_response = "This is not valid JSON"
        llm_client = MockLLMClient(llm_response)
        detector = SchemaDetector(llm_client)
        
        df = pd.DataFrame({
            "Date": ["2023-01-01", "2023-01-02"],
            "Amount": [100.00, 200.00],
            "Description": ["Test 1", "Test 2"]
        })
        
        with pytest.raises(ValueError, match="Failed to parse LLM response"):
            detector.detect_schema(df)
