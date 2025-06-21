import uuid

import pytest

from app.domain.models.counterparty import BatchCounterpartyResult, CounterpartyResult
from app.domain.models.transaction import CategorizationStatus


class TestCounterpartyResultModel:
    def test_counterparty_result_with_counterparty(self):
        transaction_id = uuid.uuid4()
        counterparty_id = uuid.uuid4()

        result = CounterpartyResult(
            transaction_id=transaction_id,
            counterparty_account_id=counterparty_id,
            status=CategorizationStatus.CATEGORIZED,
            confidence=0.95,
        )

        assert result.transaction_id == transaction_id
        assert result.counterparty_account_id == counterparty_id
        assert result.status == CategorizationStatus.CATEGORIZED
        assert result.confidence == 0.95
        assert result.error_message is None

    def test_counterparty_result_without_counterparty(self):
        transaction_id = uuid.uuid4()

        result = CounterpartyResult(
            transaction_id=transaction_id,
            counterparty_account_id=None,
            status=CategorizationStatus.CATEGORIZED,
            confidence=0.8,
        )

        assert result.transaction_id == transaction_id
        assert result.counterparty_account_id is None
        assert result.status == CategorizationStatus.CATEGORIZED
        assert result.confidence == 0.8
        assert result.error_message is None

    def test_counterparty_result_with_error(self):
        transaction_id = uuid.uuid4()

        result = CounterpartyResult(
            transaction_id=transaction_id,
            counterparty_account_id=None,
            status=CategorizationStatus.FAILURE,
            error_message="Account not found",
        )

        assert result.transaction_id == transaction_id
        assert result.counterparty_account_id is None
        assert result.status == CategorizationStatus.FAILURE
        assert result.error_message == "Account not found"
        assert result.confidence is None


class TestBatchCounterpartyResultModel:
    def test_batch_counterparty_result_valid(self):
        transaction_id1 = uuid.uuid4()
        transaction_id2 = uuid.uuid4()
        counterparty_id = uuid.uuid4()

        results = [
            CounterpartyResult(
                transaction_id=transaction_id1,
                counterparty_account_id=counterparty_id,
                status=CategorizationStatus.CATEGORIZED,
                confidence=0.95,
            ),
            CounterpartyResult(
                transaction_id=transaction_id2,
                counterparty_account_id=None,
                status=CategorizationStatus.FAILURE,
                error_message="No match found",
            ),
        ]

        batch_result = BatchCounterpartyResult(
            results=results,
            total_processed=2,
            successful_count=1,
            failed_count=1,
        )

        assert len(batch_result.results) == 2
        assert batch_result.total_processed == 2
        assert batch_result.successful_count == 1
        assert batch_result.failed_count == 1
        assert batch_result.success_rate == 0.5

    def test_batch_counterparty_result_success_rate_calculation(self):
        results = []

        batch_result = BatchCounterpartyResult(
            results=results,
            total_processed=0,
            successful_count=0,
            failed_count=0,
        )

        assert batch_result.success_rate == 0.0

        # Test with some successful results
        transaction_id1 = uuid.uuid4()
        transaction_id2 = uuid.uuid4()
        transaction_id3 = uuid.uuid4()

        results = [
            CounterpartyResult(
                transaction_id=transaction_id1,
                counterparty_account_id=uuid.uuid4(),
                status=CategorizationStatus.CATEGORIZED,
            ),
            CounterpartyResult(
                transaction_id=transaction_id2,
                counterparty_account_id=None,
                status=CategorizationStatus.CATEGORIZED,
            ),
            CounterpartyResult(
                transaction_id=transaction_id3,
                counterparty_account_id=None,
                status=CategorizationStatus.FAILURE,
            ),
        ]

        batch_result = BatchCounterpartyResult(
            results=results,
            total_processed=3,
            successful_count=2,
            failed_count=1,
        )

        assert batch_result.success_rate == pytest.approx(0.6667, rel=1e-3)

    def test_batch_counterparty_result_validation_errors(self):
        transaction_id = uuid.uuid4()
        results = [
            CounterpartyResult(
                transaction_id=transaction_id,
                counterparty_account_id=None,
                status=CategorizationStatus.CATEGORIZED,
            ),
        ]

        # Test mismatched results count
        with pytest.raises(ValueError, match="Results count must match total_processed"):
            BatchCounterpartyResult(
                results=results,
                total_processed=2,  # Wrong count
                successful_count=1,
                failed_count=0,
            )

        # Test mismatched successful count
        with pytest.raises(ValueError, match="successful_count must match actual successful results"):
            BatchCounterpartyResult(
                results=results,
                total_processed=1,
                successful_count=0,  # Wrong count
                failed_count=1,
            )

        # Test mismatched failed count
        with pytest.raises(ValueError, match="failed_count must match actual failed results"):
            BatchCounterpartyResult(
                results=results,
                total_processed=1,
                successful_count=1,
                failed_count=1,  # Wrong count
            )
