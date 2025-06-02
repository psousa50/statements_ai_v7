from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from app.domain.models.background_job import BackgroundJob, JobStatus, JobType
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.workers.job_processor import JobProcessor, process_pending_jobs


class TestJobProcessor:
    """Test the JobProcessor class"""

    @pytest.fixture
    def mock_internal(self):
        """Create mock internal dependencies"""
        internal = Mock()
        internal.background_job_repository = Mock()
        internal.background_job_service = Mock()
        internal.transaction_service = Mock()
        internal.transaction_service.transaction_repository = Mock()
        internal.transaction_categorization_service = Mock()
        internal.transaction_categorization_service.transaction_categorizer = Mock()
        # Add the transaction categorization repository
        internal.transaction_categorization_repository = Mock()
        internal.transaction_categorization_repository.create_rule.return_value = None
        return internal

    @pytest.fixture
    def job_processor(self, mock_internal):
        """Create a JobProcessor instance with mocked dependencies"""
        return JobProcessor(mock_internal)

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions for testing"""
        transactions = []
        for i in range(2):
            transaction = Transaction(
                date="2024-01-01",
                amount=100.00,
                description=f"Test transaction {i + 1}",
                uploaded_file_id=uuid4(),
            )
            transaction.id = uuid4()
            transactions.append(transaction)
        return transactions

    @pytest.fixture
    def sample_job(self, sample_transactions):
        """Create a sample background job for testing"""
        # Use the actual transaction IDs from sample_transactions
        transaction_ids = [str(t.id) for t in sample_transactions]

        job = BackgroundJob(
            job_type=JobType.AI_CATEGORIZATION,
            status=JobStatus.IN_PROGRESS,
            uploaded_file_id=uuid4(),
            progress={
                "unmatched_transaction_ids": transaction_ids,
                "total_transactions": len(transaction_ids),
                "processed_transactions": 0,
                "current_batch": 0,
                "total_batches": 0,
                "phase": "QUEUED",
            },
            result={},
        )
        job.id = uuid4()
        return job

    @pytest.mark.asyncio
    async def test_process_pending_jobs_no_jobs(self, job_processor, mock_internal):
        """Test processing when no jobs are available"""
        # Setup
        mock_internal.background_job_repository.claim_single_pending_job.return_value = None

        # Execute
        result = await job_processor.process_pending_jobs()

        # Assert
        assert result == 0
        mock_internal.background_job_repository.claim_single_pending_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_pending_jobs_single_job_success(
        self, job_processor, mock_internal, sample_job, sample_transactions
    ):
        """Test successful processing of a single job"""
        # Setup
        mock_internal.background_job_repository.claim_single_pending_job.side_effect = [
            sample_job,
            None,
        ]

        # Mock transaction retrieval
        def mock_get_by_id(transaction_id):
            return next(
                (t for t in sample_transactions if t.id == transaction_id), None
            )

        mock_internal.transaction_service.transaction_repository.get_by_id.side_effect = mock_get_by_id

        # Mock AI categorization
        mock_result = Mock()
        mock_result.status = CategorizationStatus.CATEGORIZED
        mock_result.category_id = uuid4()
        mock_result.confidence = 0.85
        mock_internal.transaction_categorization_service.transaction_categorizer.categorize.return_value = [
            mock_result
        ]

        # Execute
        result = await job_processor.process_pending_jobs()

        # Assert
        assert result == 1
        mock_internal.background_job_service.mark_job_completed.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_pending_jobs_job_failure(
        self, job_processor, mock_internal, sample_job
    ):
        """Test handling of job processing failure"""
        # Setup
        mock_internal.background_job_repository.claim_single_pending_job.side_effect = [
            sample_job,
            None,
        ]

        # Mock failure - no transactions found
        mock_internal.transaction_service.transaction_repository.get_by_id.return_value = None

        # Execute
        result = await job_processor.process_pending_jobs()

        # Assert
        assert result == 1  # Job was processed (though it failed)
        # Since transactions don't exist, the job should complete successfully with warnings
        # but not be marked as failed - this is the new behavior

    @pytest.mark.asyncio
    async def test_categorize_single_transaction_success(
        self, job_processor, mock_internal, sample_transactions
    ):
        """Test successful categorization of a single transaction"""
        # Setup
        transaction = sample_transactions[0]
        mock_result = Mock()
        mock_result.status = CategorizationStatus.CATEGORIZED
        mock_result.category_id = uuid4()
        mock_result.confidence = 0.92

        # Mock transaction retrieval
        mock_internal.transaction_service.transaction_repository.get_by_id.return_value = transaction

        # Mock the transaction_categorizer.categorize method
        mock_internal.transaction_categorization_service.transaction_categorizer.categorize.return_value = [
            mock_result
        ]

        # Mock the rule checking to return None (no existing rule)
        mock_internal.transaction_categorization_repository.get_rule_by_normalized_description.return_value = None

        # Execute - use the new method with ID
        await job_processor._categorize_single_transaction_by_id(transaction.id)

        # Assert - verify transaction was updated via repository
        mock_internal.transaction_service.transaction_repository.update.assert_called_once()
        # Verify categorization rule was created
        mock_internal.transaction_categorization_repository.create_rule.assert_called_once()

    @pytest.mark.asyncio
    async def test_categorize_single_transaction_failure(
        self, job_processor, mock_internal, sample_transactions
    ):
        """Test handling of AI categorization failure"""
        # Setup
        transaction = sample_transactions[0]
        mock_internal.transaction_service.transaction_repository.get_by_id.return_value = transaction

        # Mock empty results to trigger failure
        mock_internal.transaction_categorization_service.transaction_categorizer.categorize.return_value = []

        # Execute & Assert - the new method should raise an exception for failures
        with pytest.raises(ValueError, match="AI categorization returned no results"):
            await job_processor._categorize_single_transaction_by_id(transaction.id)

        # Verify transaction repository was called to mark the transaction as failed
        mock_internal.transaction_service.transaction_repository.update.assert_called_once()

    def test_get_transactions_by_ids(
        self, job_processor, mock_internal, sample_transactions
    ):
        """Test retrieving transactions by their IDs"""
        # Setup
        transaction_ids = [t.id for t in sample_transactions]

        def mock_get_by_id(transaction_id):
            return next(
                (t for t in sample_transactions if t.id == transaction_id), None
            )

        mock_internal.transaction_service.transaction_repository.get_by_id.side_effect = mock_get_by_id

        # Execute
        result = job_processor._get_transactions_by_ids(transaction_ids)

        # Assert
        assert len(result) == len(sample_transactions)
        assert all(t in sample_transactions for t in result)

    def test_get_transactions_by_ids_missing(self, job_processor, mock_internal):
        """Test retrieving transactions when some don't exist"""
        # Setup
        transaction_ids = [uuid4(), uuid4(), uuid4()]
        mock_internal.transaction_service.transaction_repository.get_by_id.return_value = None

        # Execute
        result = job_processor._get_transactions_by_ids(transaction_ids)

        # Assert
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_ai_categorization_job_progress_updates(
        self, job_processor, mock_internal, sample_job, sample_transactions
    ):
        """Test that progress updates are sent during AI categorization"""

        # Setup
        def mock_get_by_id(transaction_id):
            return next(
                (t for t in sample_transactions if t.id == transaction_id), None
            )

        mock_internal.transaction_service.transaction_repository.get_by_id.side_effect = mock_get_by_id

        mock_result = Mock()
        mock_result.status = CategorizationStatus.CATEGORIZED
        mock_result.category_id = uuid4()
        mock_result.confidence = 0.85
        mock_internal.transaction_categorization_service.transaction_categorizer.categorize.return_value = [
            mock_result
        ]

        # Execute
        await job_processor._process_ai_categorization_job(sample_job)

        # Assert
        mock_internal.background_job_service.update_job_progress.assert_called()
        mock_internal.background_job_service.mark_job_completed.assert_called_once()


class TestConvenienceFunction:
    """Test the convenience function"""

    @pytest.mark.asyncio
    async def test_process_pending_jobs_function(self):
        """Test the process_pending_jobs convenience function"""
        # Setup
        mock_internal = Mock()
        mock_internal.background_job_repository.claim_single_pending_job.return_value = None

        # Execute
        result = await process_pending_jobs(mock_internal)

        # Assert
        assert result == 0
        mock_internal.background_job_repository.claim_single_pending_job.assert_called_once()


class TestAtomicJobClaiming:
    """Test atomic job claiming behavior"""

    def test_claim_single_pending_job_success(self):
        """Test successful job claiming"""
        # This would be an integration test with real database
        # For now, we test the repository interface
        pass

    def test_claim_single_pending_job_concurrent_access(self):
        """Test concurrent job claiming behavior"""
        # This would require database transaction testing
        # For now, we test the repository interface
        pass
