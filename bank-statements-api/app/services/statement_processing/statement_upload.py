import logging
from typing import List
from uuid import UUID

from app.api.schemas import StatementUploadRequest
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.transaction import SourceType

logger = logging.getLogger("app")


class StatementUploadResult:
    def __init__(
        self,
        uploaded_file_id: str,
        transactions_saved: int,
        duplicated_transactions: int,
        total_processed: int,
        rule_based_matches: int,
        match_rate_percentage: float,
        processing_time_ms: int,
        background_job_info=None,
    ):
        self.uploaded_file_id = uploaded_file_id
        self.transactions_saved = transactions_saved
        self.duplicated_transactions = duplicated_transactions
        self.total_processed = total_processed
        self.rule_based_matches = rule_based_matches
        self.match_rate_percentage = match_rate_percentage
        self.processing_time_ms = processing_time_ms
        self.background_job_info = background_job_info


class StatementUploadService:
    def __init__(
        self,
        statement_parser,
        transaction_normalizer,
        uploaded_file_repo,
        file_analysis_metadata_repo,
        transaction_processing_orchestrator,
        statement_persistence_service,
        background_job_service,
    ):
        self.statement_parser = statement_parser
        self.transaction_normalizer = transaction_normalizer
        self.uploaded_file_repo = uploaded_file_repo
        self.file_analysis_metadata_repo = file_analysis_metadata_repo
        self.transaction_processing_orchestrator = transaction_processing_orchestrator
        self.statement_persistence_service = statement_persistence_service
        self.background_job_service = background_job_service

    def upload_and_process(
        self,
        upload_request: StatementUploadRequest,
        background_tasks=None,
        internal_deps=None,
    ) -> StatementUploadResult:
        """
        Complete statement upload and processing flow:
        1. Parse file to transaction DTOs
        2. Process DTOs (categorization, etc.)
        3. Save processed transactions to database
        4. Trigger immediate background job processing if background_tasks provided

        Args:
            upload_request: The upload request data
            background_tasks: Optional FastAPI BackgroundTasks for immediate processing
            internal_deps: Optional internal dependencies for background processing
        """
        # Step 1: Parse file to transaction DTOs (without persisting)
        transaction_dtos = self._parse_to_transaction_dtos(
            uploaded_file_id=upload_request.uploaded_file_id,
            column_mapping=upload_request.column_mapping,
            header_row_index=upload_request.header_row_index,
            data_start_row_index=upload_request.data_start_row_index,
            account_id=UUID(upload_request.account_id),
        )

        # Step 2: Process transaction DTOs (categorization, background job setup)
        processing_result = self.transaction_processing_orchestrator.process_transaction_dtos(
            transaction_dtos=transaction_dtos,
            uploaded_file_id=UUID(upload_request.uploaded_file_id),
        )

        # Step 3: Save processed transactions with all data complete
        persistence_result = self.statement_persistence_service.save_processed_transactions(
            processed_dtos=processing_result.processed_dtos,
            account_id=UUID(upload_request.account_id),
            uploaded_file_id=upload_request.uploaded_file_id,
        )

        # Step 3.5: Schedule background job for unmatched transactions (after persistence)
        background_job_info = None
        if processing_result.has_unmatched_transactions:
            # Get the persisted transaction IDs for unmatched transactions
            unmatched_transaction_ids = self._get_unmatched_transaction_ids(
                upload_request.uploaded_file_id, processing_result.processed_dtos
            )

            if unmatched_transaction_ids:
                logger.info(f"Queuing background job for {len(unmatched_transaction_ids)} unmatched transactions")

                background_job = self.background_job_service.queue_ai_categorization_job(
                    UUID(upload_request.uploaded_file_id), unmatched_transaction_ids
                )

                # Create background job info for response
                from app.domain.models.processing import BackgroundJobInfo

                background_job_info = BackgroundJobInfo(
                    job_id=background_job.id,
                    status=background_job.status,
                    remaining_transactions=len(unmatched_transaction_ids),
                    estimated_completion_seconds=len(unmatched_transaction_ids) * 2,  # Rough estimate
                    status_url=f"/api/v1/transactions/categorization-jobs/{background_job.id}/status",
                )

                # Step 4: Trigger immediate background job processing if requested
                if background_tasks and internal_deps:
                    self._trigger_immediate_processing(background_tasks, internal_deps)
                else:
                    logger.info(f"Background job {background_job.id} queued for cron processing")

        # Step 5: Save file analysis metadata for future duplicate detection
        self._save_file_analysis_metadata(
            uploaded_file_id=upload_request.uploaded_file_id,
            column_mapping=upload_request.column_mapping,
            header_row_index=upload_request.header_row_index,
            data_start_row_index=upload_request.data_start_row_index,
            account_id=UUID(upload_request.account_id),
        )

        # Step 6: Return result (background job info already set above)
        return StatementUploadResult(
            uploaded_file_id=persistence_result.uploaded_file_id,
            transactions_saved=persistence_result.transactions_saved,
            duplicated_transactions=persistence_result.duplicated_transactions,
            total_processed=processing_result.total_processed,
            rule_based_matches=processing_result.rule_based_matches,
            match_rate_percentage=processing_result.match_rate_percentage,
            processing_time_ms=processing_result.processing_time_ms,
            background_job_info=background_job_info,
        )

    def _trigger_immediate_processing(self, background_tasks, internal_deps):
        """
        Trigger immediate background job processing using FastAPI BackgroundTasks.

        This provides faster user experience by processing jobs immediately
        instead of waiting for the cron job.
        """
        try:
            from app.workers.job_processor import process_pending_jobs

            # Add the async job processor to FastAPI's background tasks
            background_tasks.add_task(process_pending_jobs, internal_deps)
            logger.info("Background job processing triggered immediately")

        except Exception as e:
            # Don't fail the upload if immediate processing fails
            logger.warning(f"Failed to trigger immediate background processing: {e}")
            logger.info("Background jobs will be processed by cron worker")

    def _parse_to_transaction_dtos(
        self,
        uploaded_file_id: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        account_id: UUID,
    ) -> List[TransactionDTO]:
        """Parse uploaded file to transaction DTOs without persisting"""
        # Get uploaded file
        uploaded_file = self.uploaded_file_repo.find_by_id(uploaded_file_id)
        file_content = uploaded_file.content
        file_type = uploaded_file.file_type

        # Parse file to dataframe
        raw_df = self.statement_parser.parse(file_content, file_type)

        # Process dataframe (header/data row handling)
        from app.services.common import process_dataframe

        processed_df = process_dataframe(raw_df, header_row_index, data_start_row_index)

        # Normalize columns
        normalized_df = self.transaction_normalizer.normalize(processed_df, column_mapping)

        # Convert to DTOs
        transaction_dtos = []
        for index, (_, row) in enumerate(normalized_df.iterrows()):
            transaction_dto = TransactionDTO(
                date=row["date"],
                amount=row["amount"],
                description=row["description"],
                statement_id=None,  # Will be set during persistence
                account_id=str(account_id),
                row_index=index,  # Assign row_index based on position in file
                sort_index=index,  # Initially same as row_index for uploaded transactions
                source_type=SourceType.UPLOAD.value,
            )
            transaction_dtos.append(transaction_dto)

        return transaction_dtos

    def _save_file_analysis_metadata(
        self,
        uploaded_file_id: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        account_id: UUID,
    ):
        """Save file analysis metadata for duplicate detection"""
        uploaded_file = self.uploaded_file_repo.find_by_id(uploaded_file_id)

        from app.services.common import compute_hash

        # Parse the file to get the dataframe for hash computation
        raw_df = self.statement_parser.parse(uploaded_file.content, uploaded_file.file_type)
        file_hash = compute_hash(uploaded_file.file_type, raw_df)

        existing_metadata = self.file_analysis_metadata_repo.find_by_hash(file_hash)
        if not existing_metadata:
            self.file_analysis_metadata_repo.save(
                file_hash=file_hash,
                column_mapping=column_mapping,
                header_row_index=header_row_index,
                data_start_row_index=data_start_row_index,
                account_id=account_id,
            )

    def _get_unmatched_transaction_ids(self, uploaded_file_id: str, processed_dtos: List[TransactionDTO]) -> List[UUID]:
        """Get transaction IDs for DTOs that were not categorized by rules"""
        # Get all persisted transactions that have unmatched categorization status
        from app.domain.models.transaction import CategorizationStatus

        # Get unmatched DTOs that should have statement_id set during persistence
        unmatched_dtos = [
            dto
            for dto in processed_dtos
            if dto.categorization_status == CategorizationStatus.UNCATEGORIZED and dto.statement_id
        ]

        if not unmatched_dtos:
            return []

        # Get statement_id from the first DTO (all should have the same statement_id)
        statement_id = UUID(unmatched_dtos[0].statement_id)

        # Query the database for transactions from this statement
        transaction_repo = self.transaction_processing_orchestrator.transaction_repository
        all_transactions = transaction_repo.get_by_statement_id(statement_id)

        # Filter to only unmatched transactions
        unmatched_ids = [t.id for t in all_transactions if t.categorization_status == CategorizationStatus.UNCATEGORIZED]

        return unmatched_ids
