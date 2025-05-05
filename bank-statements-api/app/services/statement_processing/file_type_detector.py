class StatementFileTypeDetector:
    def detect(self, file_content: bytes) -> str:
        if file_content.startswith(b"PK\x03\x04"):
            return "XLSX"

        if b"," in file_content and b"\n" in file_content:
            try:
                file_content.decode("utf-8")
                return "CSV"
            except UnicodeDecodeError:
                pass

        return "UNKNOWN"
