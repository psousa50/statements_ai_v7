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

    def persist(self, analysis_result: dict) -> dict:
        # Extract data from analysis result
        uploaded_file_id = analysis_result["uploaded_file_id"]
        file_type = analysis_result["file_type"]
        column_mapping = analysis_result["column_mapping"]
        file_hash = analysis_result["file_hash"]
        header_row_index = analysis_result["header_row_index"]
        data_start_row_index = analysis_result["data_start_row_index"]
        source_id = analysis_result.get("source_id", None)

        # Get file content from uploaded_file repository
        uploaded_file = self.uploaded_file_repo.find_by_id(uploaded_file_id)
        file_content = uploaded_file["content"]

        # Parse and normalize the data
        raw_df = self.statement_parser.parse(file_content, file_type)
        normalized_df = self.transaction_normalizer.normalize(raw_df, column_mapping)

        # Save metadata to FileAnalysisMetadata table
        self.file_analysis_metadata_repo.save(
            uploaded_file_id=uploaded_file_id,
            file_hash=file_hash,
            file_type=file_type,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
            # Removed normalized_sample as it shouldn't be stored in the metadata table
        )

        # Save transactions
        transactions = []
        for _, row in normalized_df.iterrows():
            transaction = {
                "date": row["date"],
                "amount": row["amount"],
                "description": row["description"],
                "uploaded_file_id": uploaded_file_id,
            }

            if source_id:
                transaction["source_id"] = source_id

            transactions.append(transaction)

        transactions_saved = self.transaction_repo.save_batch(transactions)

        return {
            "uploaded_file_id": uploaded_file_id,
            "transactions_saved": transactions_saved,
        }
