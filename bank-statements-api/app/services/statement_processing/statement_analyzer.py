import hashlib
import logging
import json

logger_content = logging.getLogger("app.llm.big")
logger = logging.getLogger("app")


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
                "file_hash": file_hash,
            }

        # Save the uploaded file first
        saved_file = self.uploaded_file_repo.save(filename, file_content)
        uploaded_file_id = saved_file["id"]

        # Process the file
        file_type = self.file_type_detector.detect(file_content)
        raw_df = self.statement_parser.parse(file_content, file_type)
        schema_info = self.schema_detector.detect_schema(raw_df)

        logger_content.debug(
            schema_info,
            extra={"prefix": "statement_analyzer.schema_info", "ext": "json"},
        )

        # Handle both dictionary and ConversionModel objects
        if isinstance(schema_info, dict):
            column_mapping = schema_info.get("column_mapping", {})
            header_row_index = schema_info.get("header_row_index", 0)
            data_start_row_index = schema_info.get("data_start_row_index", 1)
        else:
            # Assume it's a ConversionModel object
            column_mapping = schema_info.column_map
            header_row_index = schema_info.header_row
            data_start_row_index = schema_info.start_row

        # Process the DataFrame to use header row as columns and filter to start from start_row
        logger.debug(f"Original DataFrame shape: {raw_df.shape}")
        logger.debug(f"Header row index: {header_row_index}, Data start row index: {data_start_row_index}")

        # Make a copy to avoid modifying the original
        processed_df = raw_df.copy()

        # Set the header row as column names if header_row_index is valid
        if header_row_index > 0 and header_row_index < len(raw_df):
            # Get the header row values
            header_values = raw_df.iloc[header_row_index - 1].tolist()
            logger.debug(f"Header values: {header_values}")

            processed_df.columns = header_values
            logger.debug(f"Set columns to: {header_values}")

        # Filter to only include rows starting from start_row
        if data_start_row_index > 0 and data_start_row_index < len(processed_df):
            processed_df = processed_df.iloc[data_start_row_index:].reset_index(drop=True)
            logger.debug(f"Filtered DataFrame to start from row {data_start_row_index}")

        logger.debug(f"Processed DataFrame shape: {processed_df.shape}")
        logger.debug(f"Processed DataFrame columns: {processed_df.columns.tolist()}")

        if processed_df.empty:
            logger.warning("Processed DataFrame is empty after applying header row and data start row")

        logger_content.debug(
            processed_df.head(),
            extra={"prefix": "statement_analyzer.processed_df", "ext": "json"},
        )
        normalized_df = self.transaction_normalizer.normalize(processed_df, column_mapping)

        # Convert DataFrame to records and handle NaN values for JSON serialization
        sample_df = normalized_df.head(5).fillna("")
        sample_data = sample_df.to_dict(orient="records")

        return {
            "uploaded_file_id": uploaded_file_id,
            "file_type": file_type,
            "column_mapping": column_mapping,
            "header_row_index": header_row_index,
            "data_start_row_index": data_start_row_index,
            "sample_data": sample_data,
            "file_hash": file_hash,
        }

    def _compute_hash(self, filename: str, file_content: bytes) -> str:
        hasher = hashlib.sha256()
        hasher.update(filename.encode())
        hasher.update(file_content)
        return hasher.hexdigest()
