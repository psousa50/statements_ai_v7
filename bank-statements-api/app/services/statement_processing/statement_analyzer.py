import hashlib
import logging
from uuid import UUID

from app.domain.dto.statement_processing import AnalysisResultDTO
from app.domain.dto.uploaded_file import FileAnalysisMetadataDTO, UploadedFileDTO

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

    def analyze(self, filename: str, file_content: bytes) -> AnalysisResultDTO:
        file_hash = self._compute_hash(filename, file_content)
        existing_metadata = self.file_analysis_metadata_repo.find_by_hash(file_hash)

        if existing_metadata:
            # For duplicate files, just return the existing metadata without reprocessing
            return AnalysisResultDTO(
                uploaded_file_id=existing_metadata.uploaded_file_id,
                file_type=existing_metadata.file_type,
                column_mapping=existing_metadata.column_mapping,
                header_row_index=existing_metadata.header_row_index,
                data_start_row_index=existing_metadata.data_start_row_index,
                file_hash=file_hash,
                sample_data=None
            )

            # This code is now unreachable due to the early return above

        # Save the uploaded file first
        saved_file = self.uploaded_file_repo.save(filename, file_content)
        uploaded_file_id = saved_file.id

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

        # Normalize the dataframe
        normalized_df = self.transaction_normalizer.normalize(raw_df, column_mapping)

        # Generate sample data for UI display
        sample_data = self._generate_sample_data(normalized_df, column_mapping, header_row_index, data_start_row_index)

        self.file_analysis_metadata_repo.save(
            uploaded_file_id=UUID(uploaded_file_id),
            file_hash=file_hash,
            file_type=file_type,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
        )

        return AnalysisResultDTO(
            uploaded_file_id=uploaded_file_id,
            file_type=file_type,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
            sample_data=sample_data,
            file_hash=file_hash
        )

    def _compute_hash(self, filename: str, file_content: bytes) -> str:
        hasher = hashlib.sha256()
        hasher.update(filename.encode())
        hasher.update(file_content)
        return hasher.hexdigest()

    def _generate_sample_data(self, normalized_df, column_mapping, header_row_index, data_start_row_index):
        """Generate sample data as a list of normalized transactions for UI display"""
        # Take the first 10 rows of the normalized dataframe
        sample_rows = min(10, len(normalized_df))
        sample_df = normalized_df.head(sample_rows).fillna("")

        # Convert to list of dictionaries (records format)
        sample_data = sample_df.to_dict(orient="records")

        # Return the sample data as a list of records
        return sample_data
