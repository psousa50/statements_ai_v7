from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.api.schemas import StatementUploadRequest
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.dto.statement_upload import EnhancedTransactions, ParsedStatement, SavedStatement, ScheduledJobs
from app.services.statement_processing.statement_upload import StatementUploadResult, StatementUploadService
from app.services.transaction_rule_enhancement import EnhancementResult


class TestStatementUploadService:
    @pytest.fixture
    def mock_statement_parser(self):
        return Mock()

    @pytest.fixture
    def mock_transaction_normalizer(self):
        return Mock()

    @pytest.fixture
    def mock_uploaded_file_repo(self):
        return Mock()

    @pytest.fixture
    def mock_file_analysis_metadata_repo(self):
        return Mock()

    @pytest.fixture
    def mock_transaction_rule_enhancement_service(self):
        return Mock()

    @pytest.fixture
    def mock_statement_repo(self):
        return Mock()

    @pytest.fixture
    def mock_transaction_repo(self):
        return Mock()

    @pytest.fixture
    def mock_background_job_service(self):
        return Mock()

    @pytest.fixture
    def statement_upload_service(
        self,
        mock_statement_parser,
        mock_transaction_normalizer,
        mock_uploaded_file_repo,
        mock_file_analysis_metadata_repo,
        mock_transaction_rule_enhancement_service,
        mock_statement_repo,
        mock_transaction_repo,
        mock_background_job_service,
    ):
        return StatementUploadService(
            statement_parser=mock_statement_parser,
            transaction_normalizer=mock_transaction_normalizer,
            uploaded_file_repo=mock_uploaded_file_repo,
            file_analysis_metadata_repo=mock_file_analysis_metadata_repo,
            transaction_rule_enhancement_service=mock_transaction_rule_enhancement_service,
            statement_repo=mock_statement_repo,
            transaction_repo=mock_transaction_repo,
            background_job_service=mock_background_job_service,
        )

    @pytest.fixture
    def sample_upload_request(self):
        return StatementUploadRequest(
            uploaded_file_id=str(uuid4()),
            account_id=str(uuid4()),
            column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
            header_row_index=0,
            data_start_row_index=1,
        )

    def test_enhance_transactions_success(
        self,
        statement_upload_service,
        mock_transaction_rule_enhancement_service,
    ):
        """Test successful transaction enhancement"""
        # Setup test data
        parsed = ParsedStatement(
            uploaded_file_id=uuid4(),
            transaction_dtos=[
                TransactionDTO(date="2024-01-01", amount=100.0, description="Test", account_id="acc1"),
                TransactionDTO(date="2024-01-02", amount=-50.0, description="ATM", account_id="acc1"),
            ],
            account_id=uuid4(),
        )

        enhancement_result = EnhancementResult(
            enhanced_dtos=parsed.transaction_dtos,
            total_processed=2,
            rule_based_matches=1,
            match_rate_percentage=50.0,
            processing_time_ms=100,
            has_unmatched=True,
        )

        mock_transaction_rule_enhancement_service.enhance_transactions.return_value = enhancement_result

        # Execute
        result = statement_upload_service.enhance_transactions(parsed)

        # Verify
        mock_transaction_rule_enhancement_service.enhance_transactions.assert_called_once_with(parsed.transaction_dtos)
        
        assert isinstance(result, EnhancedTransactions)
        assert result.enhanced_dtos == parsed.transaction_dtos
        assert result.total_processed == 2
        assert result.rule_based_matches == 1
        assert result.match_rate_percentage == 50.0
        assert result.processing_time_ms == 100
        assert result.has_unmatched is True

    def test_build_result(self, statement_upload_service):
        """Test _build_result method"""
        enhanced = EnhancedTransactions(
            enhanced_dtos=[],
            total_processed=5,
            rule_based_matches=3,
            match_rate_percentage=60.0,
            processing_time_ms=150,
            has_unmatched=True,
        )
        
        uploaded_file_id = str(uuid4())
        saved = SavedStatement(
            statement=Mock(),
            uploaded_file_id=uploaded_file_id,
            transactions_saved=4,
            duplicated_transactions=1,
        )
        
        categorization_job_info = Mock()
        jobs = ScheduledJobs(categorization_job_info=categorization_job_info)
        
        result = statement_upload_service._build_result(enhanced, saved, jobs)
        
        assert isinstance(result, StatementUploadResult)
        assert result.uploaded_file_id == uploaded_file_id
        assert result.transactions_saved == 4
        assert result.duplicated_transactions == 1
        assert result.total_processed == 5
        assert result.rule_based_matches == 3
        assert result.match_rate_percentage == 60.0
        assert result.processing_time_ms == 150
        assert result.background_job_info == categorization_job_info

    def test_schedule_jobs_with_unmatched_transactions(
        self,
        statement_upload_service,
        mock_background_job_service,
    ):
        """Test job scheduling when there are unmatched transactions"""
        # Setup test data
        statement_id = uuid4()
        saved = SavedStatement(
            statement=Mock(id=statement_id, uploaded_file_id=uuid4()),
            uploaded_file_id=str(uuid4()),
            transactions_saved=2,
            duplicated_transactions=0,
        )

        enhanced = EnhancedTransactions(
            enhanced_dtos=[],
            total_processed=2,
            rule_based_matches=1,
            match_rate_percentage=50.0,
            processing_time_ms=100,
            has_unmatched=True,
        )

        # Mock the transaction repository calls directly
        mock_transaction_repo = statement_upload_service.transaction_repo
        
        # Mock transactions returned from repository
        from app.domain.models.transaction import CategorizationStatus
        
        unmatched_transaction = Mock()
        unmatched_transaction.id = uuid4()
        unmatched_transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
        
        all_transaction = Mock()
        all_transaction.id = uuid4()
        
        mock_transaction_repo.get_by_statement_id.return_value = [unmatched_transaction, all_transaction]

        # Mock background job responses
        categorization_job = Mock(id=uuid4(), status="PENDING")
        counterparty_job = Mock(id=uuid4(), status="PENDING")
        
        mock_background_job_service.queue_ai_categorization_job.return_value = categorization_job
        mock_background_job_service.queue_ai_counterparty_identification_job.return_value = counterparty_job

        result = statement_upload_service.schedule_jobs(saved, enhanced)

        # Verify job scheduling calls
        mock_background_job_service.queue_ai_categorization_job.assert_called_once()
        mock_background_job_service.queue_ai_counterparty_identification_job.assert_called_once()

        # Verify result
        assert isinstance(result, ScheduledJobs)
        assert result.has_categorization_job
        assert result.has_counterparty_job
        assert result.categorization_job_info.job_id == categorization_job.id
        assert result.counterparty_job_info.job_id == counterparty_job.id

    def test_schedule_jobs_without_unmatched_transactions(
        self,
        statement_upload_service,
        mock_background_job_service,
    ):
        """Test job scheduling when all transactions are matched"""
        # Setup test data
        statement_id = uuid4()
        saved = SavedStatement(
            statement=Mock(id=statement_id, uploaded_file_id=uuid4()),
            uploaded_file_id=str(uuid4()),
            transactions_saved=2,
            duplicated_transactions=0,
        )

        enhanced = EnhancedTransactions(
            enhanced_dtos=[],
            total_processed=2,
            rule_based_matches=2,
            match_rate_percentage=100.0,
            processing_time_ms=100,
            has_unmatched=False,  # No unmatched transactions
        )

        # Mock the transaction repository calls directly
        mock_transaction_repo = statement_upload_service.transaction_repo
        
        # Mock only matched transactions
        matched_transaction = Mock()
        matched_transaction.id = uuid4()
        
        mock_transaction_repo.get_by_statement_id.return_value = [matched_transaction, matched_transaction]

        counterparty_job = Mock(id=uuid4(), status="PENDING")
        mock_background_job_service.queue_ai_counterparty_identification_job.return_value = counterparty_job

        result = statement_upload_service.schedule_jobs(saved, enhanced)

        # Verify only counterparty job was scheduled
        mock_background_job_service.queue_ai_categorization_job.assert_not_called()
        mock_background_job_service.queue_ai_counterparty_identification_job.assert_called_once()

        # Verify result
        assert isinstance(result, ScheduledJobs)
        assert not result.has_categorization_job
        assert result.has_counterparty_job
        assert result.categorization_job_info is None
        assert result.counterparty_job_info.job_id == counterparty_job.id

    def test_upload_and_process_backward_compatibility(
        self,
        statement_upload_service,
        sample_upload_request,
    ):
        """Test that upload_and_process delegates to upload_statement method"""
        # Create a simple spy to verify the method delegation
        original_upload_statement = statement_upload_service.upload_statement
        
        call_count = 0
        call_args = None
        call_kwargs = None
        
        def mock_upload_statement(*args, **kwargs):
            nonlocal call_count, call_args, call_kwargs
            call_count += 1
            call_args = args
            call_kwargs = kwargs
            # Return a simple result
            return StatementUploadResult(
                uploaded_file_id=sample_upload_request.uploaded_file_id,
                transactions_saved=1,
                duplicated_transactions=0,
                total_processed=1,
                rule_based_matches=1,
                match_rate_percentage=100.0,
                processing_time_ms=50,
                background_job_info=None,
            )
        
        # Replace the method temporarily
        statement_upload_service.upload_statement = mock_upload_statement
        
        try:
            result = statement_upload_service.upload_and_process(sample_upload_request)
            
            # Verify delegation happened
            assert call_count == 1
            assert call_args[0] == sample_upload_request  # First argument should be upload_request
            assert call_kwargs.get('background_tasks') is None
            assert call_kwargs.get('internal_deps') is None
            
            # Verify result
            assert isinstance(result, StatementUploadResult)
            assert result.uploaded_file_id == sample_upload_request.uploaded_file_id
            assert result.transactions_saved == 1
            
        finally:
            # Restore original method
            statement_upload_service.upload_statement = original_upload_statement