import logging
from typing import Optional, Tuple

import pandas as pd

from app.domain.dto.statement_processing import AnalysisResultDTO
from app.services.common import compute_hash, process_dataframe
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

        # Calculate transaction statistics from the normalized data
        transaction_stats = self._calculate_transaction_statistics(
            raw_df,
            conversion_model.column_map,
            conversion_model.header_row,
            conversion_model.start_row,
        )

        source_id = existing_metadata.source_id if existing_metadata else None

        return AnalysisResultDTO(
            uploaded_file_id=uploaded_file_id,
            file_type=file_type,
            column_mapping=conversion_model.column_map,
            header_row_index=conversion_model.header_row,
            data_start_row_index=conversion_model.start_row,
            sample_data=sample_data,
            source_id=source_id,
            **transaction_stats,  # Unpack the statistics dictionary
        )

    def _generate_sample_data(self, raw_df):
        rows_as_lists = []

        column_names_row = [str(col) for col in raw_df.columns.tolist()]
        rows_as_lists.append(column_names_row)

        for _, row in raw_df.iloc[:10].iterrows():
            row_as_list = []
            for val in row.values:
                if pd.isna(val) or val is None:
                    row_as_list.append("")
                else:
                    row_as_list.append(str(val))
            rows_as_lists.append(row_as_list)

        return rows_as_lists

    def _calculate_transaction_statistics(
        self,
        raw_df: pd.DataFrame,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
    ) -> dict:
        """
        Calculate transaction statistics from the raw dataframe.

        Returns:
            Dictionary with transaction statistics including totals, duplicates, date range, and amounts
        """
        try:
            # Process the dataframe the same way as during upload
            processed_df = process_dataframe(
                raw_df, header_row_index, data_start_row_index
            )

            # Normalize the data to get proper transaction format
            normalized_df = self.transaction_normalizer.normalize(
                processed_df, column_mapping
            )

            # Calculate basic statistics
            total_transactions = len(normalized_df)

            # Calculate unique transactions based on date, amount, and description
            unique_df = normalized_df.drop_duplicates(
                subset=["date", "amount", "description"]
            )
            unique_transactions = len(unique_df)
            duplicate_transactions = total_transactions - unique_transactions

            # Calculate date range
            date_range = ("", "")
            if "date" in normalized_df.columns and len(normalized_df) > 0:
                dates = pd.to_datetime(normalized_df["date"], errors="coerce")
                valid_dates = dates.dropna()
                if len(valid_dates) > 0:
                    min_date = valid_dates.min().strftime("%Y-%m-%d")
                    max_date = valid_dates.max().strftime("%Y-%m-%d")
                    date_range = (min_date, max_date)

            # Calculate amount statistics
            total_amount = 0.0
            total_debit = 0.0
            total_credit = 0.0
            if "amount" in normalized_df.columns and len(normalized_df) > 0:
                amounts = pd.to_numeric(normalized_df["amount"], errors="coerce")
                valid_amounts = amounts.dropna()
                if len(valid_amounts) > 0:
                    total_amount = float(valid_amounts.sum())
                    # Split into debit (negative) and credit (positive)
                    debit_amounts = valid_amounts[valid_amounts < 0]
                    credit_amounts = valid_amounts[valid_amounts > 0]
                    total_debit = (
                        float(debit_amounts.sum()) if len(debit_amounts) > 0 else 0.0
                    )
                    total_credit = (
                        float(credit_amounts.sum()) if len(credit_amounts) > 0 else 0.0
                    )

            return {
                "total_transactions": total_transactions,
                "unique_transactions": unique_transactions,
                "duplicate_transactions": duplicate_transactions,
                "date_range": date_range,
                "total_amount": total_amount,
                "total_debit": total_debit,
                "total_credit": total_credit,
            }
        except Exception as e:
            logger.warning(f"Failed to calculate transaction statistics: {str(e)}")
            # Return default values if calculation fails
            return {
                "total_transactions": 0,
                "unique_transactions": 0,
                "duplicate_transactions": 0,
                "date_range": ("", ""),
                "total_amount": 0.0,
                "total_debit": 0.0,
                "total_credit": 0.0,
            }
