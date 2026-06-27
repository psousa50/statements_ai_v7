from app.services.statement_processing.text_decoding import decode_statement_bytes


class StatementFileTypeDetector:
    def detect(self, file_content: bytes) -> str:
        if file_content.startswith(b"PK\x03\x04"):
            return "XLSX"

        if b"\n" not in file_content:
            return "UNKNOWN"

        try:
            header = decode_statement_bytes(file_content).splitlines()[0]
        except IndexError:
            return "UNKNOWN"

        if "\t" in header:
            return "TSV"
        if "," in header:
            return "CSV"

        return "UNKNOWN"
