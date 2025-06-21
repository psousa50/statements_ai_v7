import logging
from typing import List
from uuid import UUID

from app.domain.dto.statement_processing import PersistenceRequestDTO, PersistenceResultDTO, TransactionDTO
from app.domain.models.transaction import SourceType
from app.services.common import compute_hash, process_dataframe

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
        account_id = persistence_request.account_id

        uploaded_file = self.uploaded_file_repo.find_by_id(uploaded_file_id)
        file_content = uploaded_file.content
        file_type = uploaded_file.file_type

        raw_df = self.statement_parser.parse(file_content, file_type)

        processed_df = process_dataframe(raw_df, header_row_index, data_start_row_index)

        normalized_df = self.transaction_normalizer.normalize(processed_df, column_mapping)

        transactions = []
        for index, (_, row) in enumerate(normalized_df.iterrows()):
            transaction = TransactionDTO(
                date=row["date"],
                amount=row["amount"],
                description=row["description"],
                uploaded_file_id=uploaded_file_id,
                account_id=account_id,
                row_index=index,  # Assign row_index based on position in file
                sort_index=index,  # Initially same as row_index for uploaded transactions
                source_type=SourceType.UPLOAD.value,
            )
            transactions.append(transaction)

        transactions_saved, duplicated_transactions = self.transaction_repo.save_batch(transactions)

        file_hash = compute_hash(file_type, raw_df)
        existing_metadata = self.file_analysis_metadata_repo.find_by_hash(file_hash)
        if not existing_metadata:
            self.file_analysis_metadata_repo.save(
                file_hash=file_hash,
                column_mapping=column_mapping,
                header_row_index=header_row_index,
                data_start_row_index=data_start_row_index,
                account_id=account_id,
            )

        return PersistenceResultDTO(
            uploaded_file_id=uploaded_file_id,
            transactions_saved=transactions_saved,
            duplicated_transactions=duplicated_transactions,
        )

    def save_processed_transactions(
        self,
        processed_dtos: List[TransactionDTO],
        account_id: UUID,
        uploaded_file_id: str,
    ) -> PersistenceResultDTO:
        """
        Save already processed transaction DTOs to the database.
        DTOs should already contain categorization data if applicable.
        """
        logger.info(f"Saving {len(processed_dtos)} processed transaction DTOs")

        # Enrich DTOs with account_id if not already set
        for dto in processed_dtos:
            if not dto.account_id:
                dto.account_id = str(account_id)
            # Ensure row_index and sort_index are set for uploaded transactions
            if dto.row_index is None:
                dto.row_index = 0  # Default fallback
            if dto.sort_index is None:
                dto.sort_index = dto.row_index  # Default to row_index for uploaded transactions
            if not dto.source_type:
                dto.source_type = SourceType.UPLOAD.value

        # Save the batch of DTOs
        transactions_saved, duplicated_transactions = self.transaction_repo.save_batch(processed_dtos)

        return PersistenceResultDTO(
            uploaded_file_id=uploaded_file_id,
            transactions_saved=transactions_saved,
            duplicated_transactions=duplicated_transactions,
        )
