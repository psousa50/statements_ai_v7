import logging

from app.domain.dto.statement_processing import AnalysisResultDTO
from app.services.common import compute_hash

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
        file_hash = compute_hash(filename, file_content)
        existing_metadata = self.file_analysis_metadata_repo.find_by_hash(file_hash)

        if existing_metadata:
            raw_df = self.statement_parser.parse(file_content, existing_metadata.file_type)
            file_type = existing_metadata.file_type
            schema_info = self.schema_detector.detect_schema(raw_df)

            column_mapping = schema_info.column_map
            header_row_index = schema_info.header_row
            data_start_row_index = schema_info.start_row
        else:
            file_type = self.file_type_detector.detect(file_content)
            raw_df = self.statement_parser.parse(file_content, file_type)
            schema_info = self.schema_detector.detect_schema(raw_df)

            column_mapping = schema_info.column_map
            header_row_index = schema_info.header_row
            data_start_row_index = schema_info.start_row

        saved_file = self.uploaded_file_repo.save(filename, file_content, file_type)
        uploaded_file_id = saved_file.id

        sample_data = self._generate_sample_data(raw_df)

        return AnalysisResultDTO(
            uploaded_file_id=uploaded_file_id,
            file_type=file_type,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
            sample_data=sample_data,
        )

    def _generate_sample_data(self, raw_df):
        rows_as_lists = []

        column_names_row = [str(col) for col in raw_df.columns.tolist()]
        rows_as_lists.append(column_names_row)

        for _, row in raw_df.iloc[:10].iterrows():
            row_as_list = [str(val) if val is not None else "" for val in row.values]
            rows_as_lists.append(row_as_list)

        return rows_as_lists
