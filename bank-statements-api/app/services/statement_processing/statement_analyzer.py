import logging

from app.domain.dto.statement_processing import AnalysisResultDTO
from app.services.common import compute_hash
from app.services.schema_detection.schema_detector import ConversionModel

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

        file_type = self.file_type_detector.detect(file_content)
        if existing_metadata:
            raw_df = self.statement_parser.parse(file_content, file_type)
            conversion_model = ConversionModel(
                column_map=existing_metadata.column_mapping,
                header_row=existing_metadata.header_row_index,
                start_row=existing_metadata.data_start_row_index,
            )
        else:
            raw_df = self.statement_parser.parse(file_content, file_type)
            conversion_model = self.schema_detector.detect_schema(raw_df)

        saved_file = self.uploaded_file_repo.save(filename, file_content, file_type)
        uploaded_file_id = saved_file.id

        sample_data = self._generate_sample_data(raw_df)

        source_id = existing_metadata.source_id if existing_metadata else None
        
        return AnalysisResultDTO(
            uploaded_file_id=uploaded_file_id,
            file_type=file_type,
            column_mapping=conversion_model.column_map,
            header_row_index=conversion_model.header_row,
            data_start_row_index=conversion_model.start_row,
            sample_data=sample_data,
            source_id=source_id,
        )

    def existing_metadata_to_schema_info(self, existing_metadata):
        return SchemaInfo(
            header_row=existing_metadata.header_row_index,
            start_row=existing_metadata.data_start_row_index,
            column_map=existing_metadata.column_mapping,
        )

    def _generate_sample_data(self, raw_df):
        rows_as_lists = []

        column_names_row = [str(col) for col in raw_df.columns.tolist()]
        rows_as_lists.append(column_names_row)

        for _, row in raw_df.iloc[:10].iterrows():
            row_as_list = [str(val) if val is not None else "" for val in row.values]
            rows_as_lists.append(row_as_list)

        return rows_as_lists
