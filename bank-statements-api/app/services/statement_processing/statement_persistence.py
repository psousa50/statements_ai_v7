from app.domain.dto.statement_processing import AnalysisResultDTO, PersistenceResultDTO, TransactionDTO


class StatementPersistenceService:
    def __init__(
        self,
        statement_parser,
        transaction_normalizer,
        transaction_repo,
        uploaded_file_repo,
        file_analysis_metadata_repo,
    ):
        self.statement_parser = statement_parser
        self.transaction_normalizer = transaction_normalizer
        self.transaction_repo = transaction_repo
        self.uploaded_file_repo = uploaded_file_repo
        self.file_analysis_metadata_repo = file_analysis_metadata_repo

    def persist(self, analysis_result: AnalysisResultDTO) -> PersistenceResultDTO:
        import logging

        logger = logging.getLogger("app")

        uploaded_file_id = analysis_result.uploaded_file_id
        file_type = analysis_result.file_type
        column_mapping = analysis_result.column_mapping
        file_hash = analysis_result.file_hash
        header_row_index = analysis_result.header_row_index
        data_start_row_index = analysis_result.data_start_row_index
        source_id = getattr(analysis_result, 'source_id', None)

        logger.info(f"Processing statement with column mapping: {column_mapping}")
        logger.info(f"Header row index: {header_row_index}, Data start row index: {data_start_row_index}")

        uploaded_file = self.uploaded_file_repo.find_by_id(uploaded_file_id)
        file_content = uploaded_file.content

        raw_df = self.statement_parser.parse(file_content, file_type)

        processed_df = self._process_dataframe(raw_df, header_row_index, data_start_row_index)

        normalized_df = self.transaction_normalizer.normalize(processed_df, column_mapping)

        existing_metadata = self.file_analysis_metadata_repo.find_by_hash(file_hash)
        if not existing_metadata:
            self.file_analysis_metadata_repo.save(
                uploaded_file_id=uploaded_file_id,
                file_hash=file_hash,
                file_type=file_type,
                column_mapping=column_mapping,
                header_row_index=header_row_index,
                data_start_row_index=data_start_row_index,
            )

        transactions = []
        for _, row in normalized_df.iterrows():
            transaction = TransactionDTO(
                date=row["date"],
                amount=row["amount"],
                description=row["description"],
                uploaded_file_id=uploaded_file_id,
                source_id=source_id
            )
            transactions.append(transaction)

        transactions_saved = self.transaction_repo.save_batch(transactions)

        return PersistenceResultDTO(
            uploaded_file_id=uploaded_file_id,
            transactions_saved=transactions_saved
        )

    def _process_dataframe(self, raw_df, header_row_index, data_start_row_index):
        processed_df = raw_df.copy()

        if header_row_index > 0 and header_row_index < len(raw_df):
            header_values = raw_df.iloc[header_row_index - 1].tolist()
            processed_df.columns = header_values

        if data_start_row_index > 0 and data_start_row_index < len(processed_df):
            processed_df = processed_df.iloc[data_start_row_index:].reset_index(drop=True)

        return processed_df
