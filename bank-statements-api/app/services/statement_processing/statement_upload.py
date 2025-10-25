import logging
from typing import List, Optional
from uuid import UUID

from app.api.schemas import StatementUploadRequest
from app.domain.dto.statement_processing import FilterCondition, RowFilter, TransactionDTO
from app.domain.dto.statement_upload import EnhancedTransactions, ParsedStatement, SavedStatement, ScheduledJobs
from app.domain.models.transaction import SourceType
from app.services.statement_processing.row_filter_service import RowFilterService
from app.services.transaction_rule_enhancement import TransactionRuleEnhancementService

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
        transaction_rule_enhancement_service: TransactionRuleEnhancementService,
        statement_repo,
        transaction_repo,
        background_job_service,
        row_filter_service: RowFilterService = None,
    ):
        self.statement_parser = statement_parser
        self.transaction_normalizer = transaction_normalizer
        self.uploaded_file_repo = uploaded_file_repo
        self.file_analysis_metadata_repo = file_analysis_metadata_repo
        self.transaction_rule_enhancement_service = transaction_rule_enhancement_service
        self.statement_repo = statement_repo
        self.transaction_repo = transaction_repo
        self.background_job_service = background_job_service
        self.row_filter_service = row_filter_service or RowFilterService()

    def upload_statement(
        self,
        upload_request: StatementUploadRequest,
        background_tasks=None,
        internal_deps=None,
    ) -> StatementUploadResult:
        """
        Simplified statement upload process with 4 clear steps:
        1. Parse statement file
        2. Enhance transactions with rule-based processing
        3. Save statement and transactions to database
        4. Schedule background jobs for AI processing
        """
        # Step 1: Parse Statement
        parsed = self.parse_statement(upload_request)

        # Step 2: Enhance Transactions
        enhanced = self.enhance_transactions(parsed)

        # Step 3: Save Statement
        saved = self.save_statement(enhanced, upload_request)

        # Step 4: Schedule Background Jobs
        jobs = self.schedule_jobs(saved, enhanced)

        # Optional: Trigger immediate processing if requested
        if background_tasks and internal_deps:
            self._trigger_immediate_processing(background_tasks, internal_deps)

        return self._build_result(enhanced, saved, jobs)

    def parse_statement(self, upload_request: StatementUploadRequest) -> ParsedStatement:
        """Step 1: Parse uploaded file to transaction DTOs"""
        logger.info(f"Parsing statement file {upload_request.uploaded_file_id}")

        # Get uploaded file
        uploaded_file = self.uploaded_file_repo.find_by_id(upload_request.uploaded_file_id)
        file_content = uploaded_file.content
        file_type = uploaded_file.file_type

        # Parse file to dataframe
        raw_df = self.statement_parser.parse(file_content, file_type)

        # Process dataframe (header/data row handling)
        from app.services.common import process_dataframe

        processed_df = process_dataframe(
            raw_df,
            upload_request.header_row_index,
            upload_request.data_start_row_index,
        )

        # Check for saved row filters if none provided in request
        row_filters_to_apply = upload_request.row_filters
        if not row_filters_to_apply:
            # Check if we have saved row filters for this file
            from app.services.common import compute_hash

            file_hash = compute_hash(file_type, raw_df)
            existing_metadata = self.file_analysis_metadata_repo.find_by_hash(file_hash)
            if existing_metadata and existing_metadata.row_filters:
                logger.info(f"Using saved row filters for file hash {file_hash}")
                # Convert saved filters back to API format
                from app.api.schemas import FilterConditionRequest, RowFilterRequest
                from app.domain.dto.statement_processing import FilterOperator, LogicalOperator

                conditions = []
                for saved_filter in existing_metadata.row_filters:
                    conditions.append(
                        FilterConditionRequest(
                            column_name=saved_filter["column_name"],
                            operator=FilterOperator(saved_filter["operator"]),
                            value=saved_filter["value"],
                            case_sensitive=saved_filter["case_sensitive"],
                        )
                    )

                row_filters_to_apply = RowFilterRequest(
                    conditions=conditions, logical_operator=LogicalOperator.AND  # Default logical operator
                )

        # Apply row filters if available (BEFORE column normalization)
        if row_filters_to_apply:
            # Convert API model to domain model
            filter_conditions = []
            for condition_request in row_filters_to_apply.conditions:
                filter_conditions.append(
                    FilterCondition(
                        column_name=condition_request.column_name,
                        operator=condition_request.operator,
                        value=condition_request.value,
                        case_sensitive=condition_request.case_sensitive,
                    )
                )

            row_filter = RowFilter(conditions=filter_conditions, logical_operator=row_filters_to_apply.logical_operator)

            # Apply the filter to the processed dataframe (with original column names)
            original_count = len(processed_df)
            processed_df = self.row_filter_service.apply_filters(processed_df, row_filter)
            filtered_count = len(processed_df)

            logger.info(f"Row filtering applied: {original_count} -> {filtered_count} rows")

        # Normalize columns (after filtering)
        normalized_df = self.transaction_normalizer.normalize(processed_df, upload_request.column_mapping)

        # Convert to DTOs
        transaction_dtos = []
        for index, (_, row) in enumerate(normalized_df.iterrows()):
            transaction_dto = TransactionDTO(
                date=row["date"],
                amount=row["amount"],
                description=row["description"],
                statement_id=None,  # Will be set during persistence
                account_id=upload_request.account_id,
                row_index=index,  # Assign row_index based on position in file
                sort_index=index,  # Initially same as row_index for uploaded transactions
                source_type=SourceType.UPLOAD.value,
            )
            transaction_dtos.append(transaction_dto)

        return ParsedStatement(
            uploaded_file_id=UUID(upload_request.uploaded_file_id),
            transaction_dtos=transaction_dtos,
            account_id=UUID(upload_request.account_id),
        )

    def enhance_transactions(self, parsed: ParsedStatement) -> EnhancedTransactions:
        """Step 2: Enhance transactions with rule-based processing"""
        logger.info(f"Enhancing {len(parsed.transaction_dtos)} transactions")

        enhancement_result = self.transaction_rule_enhancement_service.enhance_transactions(parsed.transaction_dtos)

        return EnhancedTransactions(
            enhanced_dtos=enhancement_result.enhanced_dtos,
            total_processed=enhancement_result.total_processed,
            rule_based_matches=enhancement_result.rule_based_matches,
            match_rate_percentage=enhancement_result.match_rate_percentage,
            processing_time_ms=enhancement_result.processing_time_ms,
            has_unmatched=enhancement_result.has_unmatched,
        )

    def save_statement(
        self,
        enhanced: EnhancedTransactions,
        upload_request: StatementUploadRequest,
    ) -> SavedStatement:
        """Step 3: Save statement and transactions to database"""
        logger.info(f"Saving {len(enhanced.enhanced_dtos)} transactions to database")

        # Create statement from uploaded file if transactions need to be saved
        statement = None
        transactions_saved = 0
        duplicated_transactions = 0

        if enhanced.enhanced_dtos:
            # Get uploaded file and create statement
            uploaded_file = self.uploaded_file_repo.find_by_id(upload_request.uploaded_file_id)
            statement = self.statement_repo.save(
                account_id=UUID(upload_request.account_id),
                filename=uploaded_file.filename,
                file_type=uploaded_file.file_type,
                content=uploaded_file.content,
            )

            # Enrich DTOs with required fields
            for dto in enhanced.enhanced_dtos:
                if not dto.account_id:
                    dto.account_id = upload_request.account_id
                if dto.row_index is None:
                    dto.row_index = 0  # Default fallback
                if dto.sort_index is None:
                    dto.sort_index = dto.row_index  # Default to row_index for uploaded transactions
                if not dto.source_type:
                    dto.source_type = SourceType.UPLOAD.value
                # Set statement_id on all DTOs
                dto.statement_id = str(statement.id)

            # Save the batch of DTOs
            (
                transactions_saved,
                duplicated_transactions,
            ) = self.transaction_repo.save_batch(enhanced.enhanced_dtos)

            # Update statement with transaction statistics
            self.statement_repo.update_transaction_statistics(statement.id)

        # Save file analysis metadata for future duplicate detection
        # Convert row_filters to serializable format
        row_filters_dict = None
        if upload_request.row_filters:
            row_filters_dict = [
                {
                    "column_name": condition.column_name,
                    "operator": condition.operator.value,
                    "value": condition.value,
                    "case_sensitive": condition.case_sensitive,
                }
                for condition in upload_request.row_filters.conditions
            ]

        self._save_file_analysis_metadata(
            uploaded_file_id=upload_request.uploaded_file_id,
            column_mapping=upload_request.column_mapping,
            header_row_index=upload_request.header_row_index,
            data_start_row_index=upload_request.data_start_row_index,
            account_id=UUID(upload_request.account_id),
            row_filters=row_filters_dict,
        )

        return SavedStatement(
            statement=statement,
            uploaded_file_id=upload_request.uploaded_file_id,
            transactions_saved=transactions_saved,
            duplicated_transactions=duplicated_transactions,
        )

    def schedule_jobs(
        self,
        saved: SavedStatement,
        enhanced: EnhancedTransactions,
    ) -> ScheduledJobs:
        """Step 4: Schedule background jobs for AI processing (currently disabled)"""
        # AI categorization and counterparty identification services have been removed
        # Return empty scheduled jobs
        return ScheduledJobs(
            categorization_job_info=None,
            counterparty_job_info=None,
        )

    def _build_result(
        self,
        enhanced: EnhancedTransactions,
        saved: SavedStatement,
        jobs: ScheduledJobs,
    ) -> StatementUploadResult:
        """Build the final result object"""
        return StatementUploadResult(
            uploaded_file_id=saved.uploaded_file_id,
            transactions_saved=saved.transactions_saved,
            duplicated_transactions=saved.duplicated_transactions,
            total_processed=enhanced.total_processed,
            rule_based_matches=enhanced.rule_based_matches,
            match_rate_percentage=enhanced.match_rate_percentage,
            processing_time_ms=enhanced.processing_time_ms,
            background_job_info=jobs.categorization_job_info,  # Keep main job info for response
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

    def _save_file_analysis_metadata(
        self,
        uploaded_file_id: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        account_id: UUID,
        row_filters: Optional[List[dict]] = None,
    ):
        uploaded_file = self.uploaded_file_repo.find_by_id(uploaded_file_id)

        from app.services.common import compute_hash

        raw_df = self.statement_parser.parse(uploaded_file.content, uploaded_file.file_type)
        file_hash = compute_hash(uploaded_file.file_type, raw_df)

        existing_metadata = self.file_analysis_metadata_repo.find_by_hash(file_hash)
        if existing_metadata:
            self.file_analysis_metadata_repo.update(
                file_hash=file_hash,
                column_mapping=column_mapping,
                header_row_index=header_row_index,
                data_start_row_index=data_start_row_index,
                account_id=account_id,
                row_filters=row_filters,
            )
        else:
            self.file_analysis_metadata_repo.save(
                file_hash=file_hash,
                column_mapping=column_mapping,
                header_row_index=header_row_index,
                data_start_row_index=data_start_row_index,
                account_id=account_id,
                row_filters=row_filters,
            )
