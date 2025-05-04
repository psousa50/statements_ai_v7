import pandas as pd
from abc import ABC, abstractmethod
import json


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        pass


class SchemaDetector:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def detect_schema(self, df: pd.DataFrame) -> dict:
        prompt = self._build_prompt(df)
        response = self.llm.complete(prompt)
        return self._parse_response(response)
        
    def _build_prompt(self, df: pd.DataFrame) -> str:
        sample_data = df.head(5).to_string()
        prompt = f"""
Given the following tabular data, identify:
1. The mapping of standard columns (date, amount, description) to the actual column names
2. The index of the header row (0-based)
3. The index of the first data row (0-based)

Sample data:
{sample_data}

Return your answer as a JSON object with the following structure:
{{
    "column_mapping": {{
        "date": "actual_date_column_name",
        "amount": "actual_amount_column_name",
        "description": "actual_description_column_name"
    }},
    "header_row_index": header_row_index,
    "data_start_row_index": data_start_row_index
}}
"""
        return prompt
        
    def _parse_response(self, response: str) -> dict:
        try:
            result = json.loads(response.strip())
            required_keys = ["column_mapping", "header_row_index", "data_start_row_index"]
            required_mapping_keys = ["date", "amount", "description"]
            
            if not all(key in result for key in required_keys):
                raise ValueError("Missing required keys in response")
                
            if not all(key in result["column_mapping"] for key in required_mapping_keys):
                raise ValueError("Missing required column mapping keys in response")
                
            return result
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError("Failed to parse LLM response")
