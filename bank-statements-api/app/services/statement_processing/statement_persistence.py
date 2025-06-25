import logging
from typing import List
from uuid import UUID

from app.domain.dto.statement_processing import PersistenceResultDTO, TransactionDTO
from app.domain.models.transaction import SourceType

logger = logging.getLogger("app")


class StatementPersistenceService:
    def __init__(
        self,
        statement_parser,
        transaction_normalizer,
        transaction_repo,
        uploaded_file_repo,
        file_analysis_metadata_repo,
        statement_repo,
    ):
        self.statement_parser = statement_parser
        self.transaction_normalizer = transaction_normalizer
        self.transaction_repo = transaction_repo
        self.uploaded_file_repo = uploaded_file_repo
        self.file_analysis_metadata_repo = file_analysis_metadata_repo
        self.statement_repo = statement_repo

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

        # Create statement from uploaded file if transactions need to be saved
        statement = None
        if processed_dtos:
            uploaded_file = self.uploaded_file_repo.find_by_id(uploaded_file_id)
            statement = self.statement_repo.save(
                account_id=account_id,
                filename=uploaded_file.filename,
                file_type=uploaded_file.file_type,
                content=uploaded_file.content,
            )

            # Update all DTOs with the statement_id
            for dto in processed_dtos:
                dto.statement_id = str(statement.id)

        # Save the batch of DTOs
        transactions_saved, duplicated_transactions = self.transaction_repo.save_batch(processed_dtos)

        return PersistenceResultDTO(
            uploaded_file_id=uploaded_file_id,
            transactions_saved=transactions_saved,
            duplicated_transactions=duplicated_transactions,
            statement=statement,
        )
