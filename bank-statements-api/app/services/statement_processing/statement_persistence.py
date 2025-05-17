import hashlib
import logging

from app.domain.dto.statement_processing import PersistenceRequestDTO, PersistenceResultDTO, TransactionDTO

logger = logging.getLogger("app")


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

    def persist(self, persistence_request: PersistenceRequestDTO) -> PersistenceResultDTO:
        uploaded_file_id = persistence_request.uploaded_file_id
        column_mapping = persistence_request.column_mapping
        header_row_index = persistence_request.header_row_index
        data_start_row_index = persistence_request.data_start_row_index
        source_id = persistence_request.source_id

        uploaded_file = self.uploaded_file_repo.find_by_id(uploaded_file_id)
        file_content = uploaded_file.content
        file_type = uploaded_file.file_type

        raw_df = self.statement_parser.parse(file_content, file_type)

        print(f"Raw DataFrame: {raw_df}")

        processed_df = self._process_dataframe(raw_df, header_row_index, data_start_row_index)

        print(f"Processed DataFrame: {processed_df}")

        normalized_df = self.transaction_normalizer.normalize(processed_df, column_mapping)

        print(f"Normalized DataFrame: {normalized_df}")

        transactions = []
        for _, row in normalized_df.iterrows():
            transaction = TransactionDTO(
                date=row["date"], amount=row["amount"], description=row["description"], uploaded_file_id=uploaded_file_id, source_id=source_id
            )
            transactions.append(transaction)

        for transaction in transactions:
            print(f"Saving transaction: {transaction}")

        transactions_saved = self.transaction_repo.save_batch(transactions)

        file_hash = self._compute_hash(uploaded_file.filename, file_content)
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

        return PersistenceResultDTO(uploaded_file_id=uploaded_file_id, transactions_saved=transactions_saved)

    def _compute_hash(self, filename: str, file_content: bytes) -> str:
        hasher = hashlib.sha256()
        hasher.update(filename.encode())
        hasher.update(file_content)
        return hasher.hexdigest()

    def _process_dataframe(self, raw_df, header_row_index, data_start_row_index):
        processed_df = raw_df.copy()

        if header_row_index > 0:
            header_values = raw_df.iloc[header_row_index - 1].tolist()
            processed_df.columns = header_values

        processed_df = processed_df.iloc[data_start_row_index - 1 :].reset_index(drop=True)

        return processed_df
