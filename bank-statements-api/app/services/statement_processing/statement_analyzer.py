import pandas as pd
import hashlib
import json


class StatementAnalyzerService:
    def __init__(
        self,
        file_type_detector,
        statement_parser,
        schema_detector,
        transaction_normalizer,
        uploaded_file_repo,
        file_analysis_metadata_repo,
    ):
        self.file_type_detector = file_type_detector
        self.statement_parser = statement_parser
        self.schema_detector = schema_detector
        self.transaction_normalizer = transaction_normalizer
        self.uploaded_file_repo = uploaded_file_repo
        self.file_analysis_metadata_repo = file_analysis_metadata_repo

    def analyze(self, filename: str, file_content: bytes) -> dict:
        file_hash = self._compute_hash(filename, file_content)
        existing_metadata = self.file_analysis_metadata_repo.find_by_hash(file_hash)

        if existing_metadata:
            return {
                "uploaded_file_id": existing_metadata["uploaded_file_id"],
                "file_type": existing_metadata["file_type"],
                "column_mapping": existing_metadata["column_mapping"],
                "header_row_index": existing_metadata["header_row_index"],
                "data_start_row_index": existing_metadata["data_start_row_index"],
                "sample_data": existing_metadata["normalized_sample"],
                "file_hash": file_hash
            }

        # Save the uploaded file first
        saved_file = self.uploaded_file_repo.save(filename, file_content)
        uploaded_file_id = saved_file["id"]

        # Process the file
        file_type = self.file_type_detector.detect(file_content)
        raw_df = self.statement_parser.parse(file_content, file_type)
        schema_info = self.schema_detector.detect_schema(raw_df)

        column_mapping = schema_info["column_mapping"]
        header_row_index = schema_info["header_row_index"]
        data_start_row_index = schema_info["data_start_row_index"]

        normalized_df = self.transaction_normalizer.normalize(raw_df, column_mapping)
        sample_data = normalized_df.head(5).to_dict(orient="records")

        return {
            "uploaded_file_id": uploaded_file_id,
            "file_type": file_type,
            "column_mapping": column_mapping,
            "header_row_index": header_row_index,
            "data_start_row_index": data_start_row_index,
            "sample_data": sample_data,
            "file_hash": file_hash
        }

    def _compute_hash(self, filename: str, file_content: bytes) -> str:
        hasher = hashlib.sha256()
        hasher.update(filename.encode())
        hasher.update(file_content)
        return hasher.hexdigest()
