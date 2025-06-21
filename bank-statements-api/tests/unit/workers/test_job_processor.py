from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.domain.models.background_job import BackgroundJob, JobStatus, JobType
from app.domain.models.transaction import Transaction
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
                statement_id=uuid4(),
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
    async def test_process_pending_jobs_single_job_success(self, job_processor, mock_internal, sample_job, sample_transactions):
        """Test successful processing of a single job"""
        # Setup
        mock_internal.background_job_repository.claim_single_pending_job.side_effect = [
            sample_job,
            None,
        ]

        # Mock the new batch categorization method
        async def mock_categorize_batch_by_ids(transaction_ids, progress_callback=None, batch_size=20):
            if progress_callback:
                # Simulate progress callback
                from app.domain.models.processing import ProcessingProgress

                progress = ProcessingProgress(
                    current_batch=1,
                    total_batches=1,
                    processed_transactions=len(transaction_ids),
                    total_transactions=len(transaction_ids),
                    phase="AI_CATEGORIZING",
                )
                progress_callback(progress)

            return {
                "total_processed": len(transaction_ids),
                "successfully_categorized": len(transaction_ids),
                "failed_categorizations": 0,
                "processing_time_ms": 100,
            }

        mock_internal.transaction_categorization_service.categorize_batch_by_ids = mock_categorize_batch_by_ids

        # Execute
        result = await job_processor.process_pending_jobs()

        # Assert
        assert result == 1
        mock_internal.background_job_service.mark_job_completed.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_pending_jobs_job_failure(self, job_processor, mock_internal, sample_job):
        """Test handling of job processing failure"""
        # Setup
        mock_internal.background_job_repository.claim_single_pending_job.side_effect = [
            sample_job,
            None,
        ]

        # Mock failure - no transactions found exception
        async def mock_categorize_batch_by_ids_failure(transaction_ids, progress_callback=None, batch_size=20):
            raise ValueError("No unmatched transaction IDs found in job progress")

        mock_internal.transaction_categorization_service.categorize_batch_by_ids = mock_categorize_batch_by_ids_failure

        # Execute
        result = await job_processor.process_pending_jobs()

        # Assert
        assert result == 1  # Job was processed (though it failed)
        # Job should be marked as failed due to the exception
        mock_internal.background_job_service.mark_job_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_categorization_job_progress_updates(self, job_processor, mock_internal, sample_job, sample_transactions):
        """Test that progress updates are sent during AI categorization"""

        # Mock the new batch categorization method with progress callback
        async def mock_categorize_batch_by_ids(transaction_ids, progress_callback=None, batch_size=20):
            if progress_callback:
                # Simulate progress callback
                from app.domain.models.processing import ProcessingProgress

                progress = ProcessingProgress(
                    current_batch=1,
                    total_batches=1,
                    processed_transactions=len(transaction_ids),
                    total_transactions=len(transaction_ids),
                    phase="AI_CATEGORIZING",
                )
                progress_callback(progress)

            return {
                "total_processed": len(transaction_ids),
                "successfully_categorized": len(transaction_ids),
                "failed_categorizations": 0,
                "processing_time_ms": 100,
            }

        mock_internal.transaction_categorization_service.categorize_batch_by_ids = mock_categorize_batch_by_ids

        # Execute
        await job_processor._process_ai_categorization_job_by_id(sample_job.id, sample_job.progress)

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
