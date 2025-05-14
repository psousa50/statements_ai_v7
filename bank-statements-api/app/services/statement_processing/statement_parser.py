import io

import pandas as pd


class StatementParser:
    def parse(self, file_content: bytes, file_type: str) -> pd.DataFrame:
        if file_type == "CSV":
            # Use dtype=None to allow pandas to infer the data types
            return pd.read_csv(io.BytesIO(file_content), dtype=str)
        elif file_type == "XLSX":
            return pd.read_excel(io.BytesIO(file_content), dtype=str)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
