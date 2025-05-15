import hashlib
import logging
import json
import pandas as pd
from uuid import UUID

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
            # For existing metadata, we need to regenerate the sample_data and normalized_sample
            # since they're not stored in the database

            # Get the file content to regenerate the samples
            uploaded_file = self.uploaded_file_repo.find_by_id(UUID(existing_metadata["uploaded_file_id"]))
            if not uploaded_file:
                # If file not found, return what we have without samples
                return {
                    "uploaded_file_id": existing_metadata["uploaded_file_id"],
                    "file_type": existing_metadata["file_type"],
                    "column_mapping": existing_metadata["column_mapping"],
                    "header_row_index": existing_metadata["header_row_index"],
                    "data_start_row_index": existing_metadata["data_start_row_index"],
                    "file_hash": file_hash,
                }

            # Regenerate the samples
            file_content = uploaded_file["content"]
            file_type = existing_metadata["file_type"]
            column_mapping = existing_metadata["column_mapping"]
            header_row_index = existing_metadata["header_row_index"]
            data_start_row_index = existing_metadata["data_start_row_index"]

            # Parse the file to get the raw dataframe
            raw_df = self.statement_parser.parse(file_content, file_type)

            # Generate sample_data (original file with metadata)
            sample_data = self._generate_sample_data(raw_df, column_mapping, header_row_index, data_start_row_index)

            # Process the DataFrame to use header row as columns and filter to start from start_row
            processed_df = self._process_dataframe(raw_df, header_row_index, data_start_row_index)

            return {
                "uploaded_file_id": existing_metadata["uploaded_file_id"],
                "file_type": existing_metadata["file_type"],
                "column_mapping": existing_metadata["column_mapping"],
                "header_row_index": existing_metadata["header_row_index"],
                "data_start_row_index": existing_metadata["data_start_row_index"],
                "sample_data": sample_data,
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
        processed_df = self._process_dataframe(raw_df, header_row_index, data_start_row_index)

        sample_data = self._generate_sample_data(raw_df, column_mapping, header_row_index, data_start_row_index)

        self.file_analysis_metadata_repo.save(
            uploaded_file_id=UUID(uploaded_file_id),
            file_hash=file_hash,
            file_type=file_type,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
        )

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

    def _process_dataframe(self, raw_df, header_row_index, data_start_row_index):
        """Process the DataFrame to use header row as columns and filter to start from start_row"""
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

        return processed_df

    def _generate_sample_data(self, raw_df, column_mapping, header_row_index, data_start_row_index):
        """Generate sample data as a list of lists of strings for UI display"""
        # Take the first 10 rows of the raw dataframe to show in the UI
        sample_rows = min(10, len(raw_df))
        sample_df = raw_df.head(sample_rows).fillna("")

        # Add metadata
        metadata = {
            "header_row_index": header_row_index - 1,  # Convert to 0-based index for UI
            "data_start_row_index": data_start_row_index - 1,  # Convert to 0-based index for UI
            "column_mappings": {},  # Will store column index to standard field mappings
        }

        # Create column mappings by index
        for std_field, file_col in column_mapping.items():
            if file_col and file_col != "":
                # We need to find which column contains the field name
                # Check in the header row first
                header_row_idx = header_row_index - 1
                if 0 <= header_row_idx < len(sample_df):
                    header_row = sample_df.iloc[header_row_idx].values
                    for i, val in enumerate(header_row):
                        if str(val) == file_col:
                            metadata["column_mappings"][str(i)] = std_field
                            break

        # Convert each row to a list of strings
        rows_as_lists = []

        # Add the column names as the first row
        column_names_row = [str(col) for col in raw_df.columns.tolist()]
        rows_as_lists.append(column_names_row)

        # Add the actual data rows
        for _, row in sample_df.iterrows():
            # Convert each value to string
            row_as_list = [str(val) if val is not None else "" for val in row.values]
            rows_as_lists.append(row_as_list)

        # Update header and data start row indices to account for the added column names row
        metadata["header_row_index"] += 1
        metadata["data_start_row_index"] += 1

        # Return metadata and rows
        return {"metadata": metadata, "rows": rows_as_lists}
