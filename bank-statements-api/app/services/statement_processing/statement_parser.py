import csv
import io

import pandas as pd

from app.services.statement_processing.text_decoding import decode_statement_bytes


class StatementParser:
    def parse(self, file_content: bytes, file_type: str) -> pd.DataFrame:
        if file_type == "CSV":
            return self._read_delimited(file_content, ",")
        elif file_type == "TSV":
            return self._read_delimited(file_content, "\t")
        elif file_type == "XLSX":
            return pd.read_excel(io.BytesIO(file_content), dtype=str)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _read_delimited(self, file_content: bytes, delimiter: str) -> pd.DataFrame:
        text = decode_statement_bytes(file_content)
        rows = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter) if any(field.strip() for field in row)]
        if not rows:
            return pd.DataFrame()

        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        return pd.DataFrame(rows[1:], columns=self._unique_columns(rows[0]))

    def _unique_columns(self, header: list[str]) -> list[str]:
        seen: dict[str, int] = {}
        columns = []
        for index, name in enumerate(header):
            label = name if name != "" else f"Unnamed: {index}"
            if label in seen:
                seen[label] += 1
                label = f"{label}.{seen[label]}"
            else:
                seen[label] = 0
            columns.append(label)
        return columns
