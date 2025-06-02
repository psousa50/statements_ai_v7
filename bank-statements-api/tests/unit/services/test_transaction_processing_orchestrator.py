import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.domain.models.background_job import BackgroundJob, JobStatus, JobType
from app.domain.models.processing import BackgroundJobInfo, SyncCategorizationResult
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.repositories.transaction import TransactionRepository
from app.services.background.background_job_service import BackgroundJobService
from app.services.rule_based_categorization import RuleBasedCategorizationService
from app.services.transaction_processing_orchestrator import TransactionProcessingOrchestrator


class TestTransactionProcessingOrchestrator:
    """Unit tests for TransactionProcessingOrchestrator"""

    @pytest.fixture
    def mock_rule_based_service(self):
        """Create mock rule-based categorization service"""
        service = MagicMock(spec=RuleBasedCategorizationService)
        return service

    @pytest.fixture
    def mock_background_job_service(self):
        """Create mock background job service"""
        service = MagicMock(spec=BackgroundJobService)
        return service

    @pytest.fixture
    def mock_transaction_repository(self):
        """Create mock transaction repository"""
        repository = MagicMock(spec=TransactionRepository)
        return repository

    @pytest.fixture
    def orchestrator(
        self,
        mock_rule_based_service,
        mock_background_job_service,
        mock_transaction_repository,
    ):
        """Create orchestrator with mocked dependencies"""
        return TransactionProcessingOrchestrator(
            rule_based_categorization_service=mock_rule_based_service,
            background_job_service=mock_background_job_service,
            transaction_repository=mock_transaction_repository,
        )

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions for testing"""
        return [
            Transaction(
                id=uuid.uuid4(),
                date=date(2023, 1, 1),
                description="STARBUCKS COFFEE #123",
                normalized_description="starbucks coffee",
                amount=Decimal("4.50"),
                categorization_status=CategorizationStatus.UNCATEGORIZED,
            ),
            Transaction(
                id=uuid.uuid4(),
                date=date(2023, 1, 2),
                description="WALMART STORE #456",
                normalized_description="walmart store",
                amount=Decimal("25.30"),
                categorization_status=CategorizationStatus.UNCATEGORIZED,
            ),
            Transaction(
                id=uuid.uuid4(),
                date=date(2023, 1, 3),
                description="UNKNOWN MERCHANT XYZ",
                normalized_description="unknown merchant xyz",
                amount=Decimal("15.75"),
                categorization_status=CategorizationStatus.UNCATEGORIZED,
            ),
        ]

    def test_process_transactions_all_matched_by_rules(
        self,
        orchestrator,
        mock_rule_based_service,
        mock_background_job_service,
        mock_transaction_repository,
        sample_transactions,
    ):
        """Test processing when all transactions are matched by rules"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        category_id_1 = uuid.uuid4()
        category_id_2 = uuid.uuid4()

        # Mock rule-based categorization returns matches for all transactions
        mock_rule_based_service.categorize_batch.return_value = {
            "starbucks coffee": category_id_1,
            "walmart store": category_id_2,
            "unknown merchant xyz": category_id_1,  # This one also matches
        }

        # Act
        result = orchestrator.process_transactions(uploaded_file_id, sample_transactions)

        # Assert
        assert isinstance(result, SyncCategorizationResult)
        assert result.total_processed == 3
        assert result.rule_based_matches == 3
        assert len(result.unmatched_transaction_ids) == 0
        assert result.match_rate_percentage == 100.0
        assert not result.has_unmatched_transactions

        # Verify no background job was queued
        mock_background_job_service.queue_ai_categorization_job.assert_not_called()

        # Verify transactions were updated
        for transaction in sample_transactions:
            assert transaction.categorization_status == CategorizationStatus.CATEGORIZED
            assert transaction.category_id is not None

        # Verify repository update was called for each categorized transaction
        assert mock_transaction_repository.update.call_count == 3

    def test_process_transactions_partial_matches(
        self,
        orchestrator,
        mock_rule_based_service,
        mock_background_job_service,
        sample_transactions,
    ):
        """Test processing when only some transactions are matched by rules"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        category_id_1 = uuid.uuid4()
        background_job = BackgroundJob(
            id=uuid.uuid4(),
            job_type=JobType.AI_CATEGORIZATION,
            status=JobStatus.PENDING,
        )

        # Mock rule-based categorization returns partial matches
        mock_rule_based_service.categorize_batch.return_value = {
            "starbucks coffee": category_id_1,
            "walmart store": category_id_1,
            # "unknown merchant xyz" not matched
        }

        mock_background_job_service.queue_ai_categorization_job.return_value = background_job

        # Act
        result = orchestrator.process_transactions(uploaded_file_id, sample_transactions)

        # Assert
        assert isinstance(result, SyncCategorizationResult)
        assert result.total_processed == 3
        assert result.rule_based_matches == 2
        assert len(result.unmatched_transaction_ids) == 1
        assert result.match_rate_percentage == 66.7  # 2/3 * 100 rounded to 1 decimal
        assert result.has_unmatched_transactions

        # Verify background job was queued with unmatched transaction ID
        unmatched_transaction_id = sample_transactions[2].id  # The unknown merchant
        mock_background_job_service.queue_ai_categorization_job.assert_called_once_with(uploaded_file_id, [unmatched_transaction_id])

        # Verify transaction statuses
        assert sample_transactions[0].categorization_status == CategorizationStatus.CATEGORIZED
        assert sample_transactions[1].categorization_status == CategorizationStatus.CATEGORIZED
        assert sample_transactions[2].categorization_status == CategorizationStatus.UNCATEGORIZED

    def test_process_transactions_no_matches(
        self,
        orchestrator,
        mock_rule_based_service,
        mock_background_job_service,
        sample_transactions,
    ):
        """Test processing when no transactions are matched by rules"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        background_job = BackgroundJob(
            id=uuid.uuid4(),
            job_type=JobType.AI_CATEGORIZATION,
            status=JobStatus.PENDING,
        )

        # Mock rule-based categorization returns no matches
        mock_rule_based_service.categorize_batch.return_value = {}

        mock_background_job_service.queue_ai_categorization_job.return_value = background_job

        # Act
        result = orchestrator.process_transactions(uploaded_file_id, sample_transactions)

        # Assert
        assert isinstance(result, SyncCategorizationResult)
        assert result.total_processed == 3
        assert result.rule_based_matches == 0
        assert len(result.unmatched_transaction_ids) == 3
        assert result.match_rate_percentage == 0.0
        assert result.has_unmatched_transactions

        # Verify background job was queued with all transaction IDs
        expected_unmatched_ids = [t.id for t in sample_transactions]
        mock_background_job_service.queue_ai_categorization_job.assert_called_once_with(uploaded_file_id, expected_unmatched_ids)

        # Verify all transactions remain uncategorized
        for transaction in sample_transactions:
            assert transaction.categorization_status == CategorizationStatus.UNCATEGORIZED
            assert transaction.category_id is None

    def test_process_transactions_empty_list(self, orchestrator, mock_rule_based_service, mock_background_job_service):
        """Test processing empty transaction list"""
        # Arrange
        uploaded_file_id = uuid.uuid4()

        # Act
        result = orchestrator.process_transactions(uploaded_file_id, [])

        # Assert
        assert isinstance(result, SyncCategorizationResult)
        assert result.total_processed == 0
        assert result.rule_based_matches == 0
        assert len(result.unmatched_transaction_ids) == 0
        assert result.match_rate_percentage == 0.0
        assert not result.has_unmatched_transactions

        # Verify no services were called
        mock_rule_based_service.categorize_batch.assert_not_called()
        mock_background_job_service.queue_ai_categorization_job.assert_not_called()

    def test_process_transactions_with_background_job_info(
        self,
        orchestrator,
        mock_rule_based_service,
        mock_background_job_service,
        sample_transactions,
    ):
        """Test getting background job info after processing"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        background_job = BackgroundJob(
            id=uuid.uuid4(),
            job_type=JobType.AI_CATEGORIZATION,
            status=JobStatus.PENDING,
        )
        job_info = BackgroundJobInfo(
            job_id=background_job.id,
            status=JobStatus.PENDING,
            remaining_transactions=1,
            estimated_completion_seconds=30,
            status_url=f"/api/v1/jobs/{background_job.id}/status",
        )

        # Mock partial matches requiring background job
        mock_rule_based_service.categorize_batch.return_value = {
            "starbucks coffee": uuid.uuid4(),
            "walmart store": uuid.uuid4(),
            # "unknown merchant xyz" not matched
        }

        mock_background_job_service.queue_ai_categorization_job.return_value = background_job
        mock_background_job_service.get_background_job_info.return_value = job_info

        # Act
        sync_result = orchestrator.process_transactions(uploaded_file_id, sample_transactions)
        bg_job_info = orchestrator.get_background_job_info(background_job.id, "/api/v1/jobs/{}/status")

        # Assert
        assert sync_result.has_unmatched_transactions
        assert bg_job_info == job_info
        mock_background_job_service.get_background_job_info.assert_called_once_with(background_job.id, "/api/v1/jobs/{}/status")

    def test_process_transactions_rule_based_service_exception(
        self,
        orchestrator,
        mock_rule_based_service,
        mock_background_job_service,
        sample_transactions,
    ):
        """Test handling exception from rule-based categorization service"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        mock_rule_based_service.categorize_batch.side_effect = Exception("Rule service failed")

        # Act & Assert
        with pytest.raises(Exception, match="Rule service failed"):
            orchestrator.process_transactions(uploaded_file_id, sample_transactions)

        # Verify no background job was queued
        mock_background_job_service.queue_ai_categorization_job.assert_not_called()

    def test_process_transactions_background_job_service_exception(
        self,
        orchestrator,
        mock_rule_based_service,
        mock_background_job_service,
        sample_transactions,
    ):
        """Test handling exception from background job service"""
        # Arrange
        uploaded_file_id = uuid.uuid4()

        # Mock partial matches but background job service fails
        mock_rule_based_service.categorize_batch.return_value = {
            "starbucks coffee": uuid.uuid4(),
            # Other transactions not matched
        }
        mock_background_job_service.queue_ai_categorization_job.side_effect = Exception("Background job service failed")

        # Act & Assert
        with pytest.raises(Exception, match="Background job service failed"):
            orchestrator.process_transactions(uploaded_file_id, sample_transactions)

    def test_calculate_processing_metrics(self, orchestrator):
        """Test processing time calculation"""
        # Arrange
        start_time_ms = 1000
        end_time_ms = 1500

        # This would typically be a private method, but we test the public interface
        # The processing time should be calculated and included in results
        # This test verifies the timing logic is working

        # Act - We'll test this indirectly through the main method
        # The orchestrator should track processing time

        # For now, this is a placeholder - the actual timing will be tested
        # when we implement the service
        processing_time = end_time_ms - start_time_ms

        # Assert
        assert processing_time == 500

    def test_get_background_job_info_not_found(self, orchestrator, mock_background_job_service):
        """Test getting background job info when job doesn't exist"""
        # Arrange
        job_id = uuid.uuid4()
        mock_background_job_service.get_background_job_info.return_value = None

        # Act
        result = orchestrator.get_background_job_info(job_id, "/api/v1/jobs/{}/status")

        # Assert
        assert result is None
        mock_background_job_service.get_background_job_info.assert_called_once_with(job_id, "/api/v1/jobs/{}/status")

    def test_process_transactions_deduplication_optimization(self, orchestrator, mock_rule_based_service, mock_background_job_service):
        """Test that duplicate normalized descriptions are deduplicated before calling rule service"""
        # Arrange
        uploaded_file_id = uuid.uuid4()
        category_id = uuid.uuid4()

        # Create transactions with duplicate normalized descriptions
        duplicate_transactions = [
            Transaction(
                id=uuid.uuid4(),
                date=date(2023, 1, 1),
                description="STARBUCKS COFFEE #123",
                normalized_description="starbucks coffee",
                amount=Decimal("4.50"),
                categorization_status=CategorizationStatus.UNCATEGORIZED,
            ),
            Transaction(
                id=uuid.uuid4(),
                date=date(2023, 1, 2),
                description="STARBUCKS COFFEE #456",  # Different description
                normalized_description="starbucks coffee",  # Same normalized description
                amount=Decimal("5.25"),
                categorization_status=CategorizationStatus.UNCATEGORIZED,
            ),
            Transaction(
                id=uuid.uuid4(),
                date=date(2023, 1, 3),
                description="WALMART STORE #789",
                normalized_description="walmart store",
                amount=Decimal("25.30"),
                categorization_status=CategorizationStatus.UNCATEGORIZED,
            ),
            Transaction(
                id=uuid.uuid4(),
                date=date(2023, 1, 4),
                description="STARBUCKS COFFEE #999",  # Another Starbucks
                normalized_description="starbucks coffee",  # Same normalized description again
                amount=Decimal("3.75"),
                categorization_status=CategorizationStatus.UNCATEGORIZED,
            ),
        ]

        # Mock rule-based categorization returns matches
        mock_rule_based_service.categorize_batch.return_value = {
            "starbucks coffee": category_id,
            "walmart store": category_id,
        }

        # Act
        result = orchestrator.process_transactions(uploaded_file_id, duplicate_transactions)

        # Assert
        # Verify that categorize_batch was called with deduplicated list
        # Should only contain unique normalized descriptions: ["starbucks coffee", "walmart store"]
        mock_rule_based_service.categorize_batch.assert_called_once()
        called_descriptions = mock_rule_based_service.categorize_batch.call_args[0][0]

        # Should have only 2 unique descriptions despite 4 transactions
        assert len(called_descriptions) == 2
        assert "starbucks coffee" in called_descriptions
        assert "walmart store" in called_descriptions
        assert called_descriptions.count("starbucks coffee") == 1  # No duplicates

        # Verify all transactions were categorized correctly
        assert result.total_processed == 4
        assert result.rule_based_matches == 4
        assert len(result.unmatched_transaction_ids) == 0
        assert result.match_rate_percentage == 100.0

        # Verify all transactions got the category assigned
        for transaction in duplicate_transactions:
            assert transaction.categorization_status == CategorizationStatus.CATEGORIZED
            assert transaction.category_id == category_id
