import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.services.recurring_expense_analyzer import ACTIVE_PATTERNS_DAYS, RecurringExpenseAnalyzer


class TestRecurringExpenseAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = RecurringExpenseAnalyzer(min_occurrences=3, amount_variance_threshold=0.15)
        self.user_id = uuid.uuid4()

    def create_transaction(
        self,
        normalized_description: str = "test transaction",
        amount: Decimal = Decimal("100.00"),
        transaction_date: date = date(2024, 1, 1),
        category_id: uuid.UUID = None,
    ) -> Transaction:
        transaction = Transaction()
        transaction.id = uuid.uuid4()
        transaction.description = normalized_description
        transaction.normalized_description = normalized_description
        transaction.amount = amount
        transaction.date = transaction_date
        transaction.category_id = category_id
        transaction.account_id = uuid.uuid4()
        transaction.categorization_status = CategorizationStatus.UNCATEGORIZED
        transaction.source_type = SourceType.UPLOAD
        transaction.sort_index = 0
        return transaction

    def test_analyze_patterns_empty_transactions(self):
        result = self.analyzer.analyze_patterns([], self.user_id)
        assert len(result.patterns) == 0
        assert result.total_monthly_recurring == Decimal("0")
        assert result.pattern_count == 0

    def test_analyze_patterns_insufficient_occurrences(self):
        transactions = [
            self.create_transaction(normalized_description="spotify", transaction_date=date(2024, 1, 1)),
            self.create_transaction(normalized_description="spotify", transaction_date=date(2024, 2, 1)),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)
        assert len(result.patterns) == 0

    def test_analyze_patterns_monthly_recurring_detected(self):
        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 1
        pattern = result.patterns[0]
        assert pattern.normalized_description == "spotify"
        assert pattern.transaction_count == 3
        assert pattern.average_amount == Decimal("9.99")
        assert pattern.amount_variance == 0.0
        assert 28 <= pattern.interval_days <= 32

    def test_analyze_patterns_multiple_recurring_expenses(self):
        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 1),
            ),
            self.create_transaction(
                normalized_description="netflix",
                amount=Decimal("15.99"),
                transaction_date=date(2024, 1, 15),
            ),
            self.create_transaction(
                normalized_description="netflix",
                amount=Decimal("15.99"),
                transaction_date=date(2024, 2, 15),
            ),
            self.create_transaction(
                normalized_description="netflix",
                amount=Decimal("15.99"),
                transaction_date=date(2024, 3, 15),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 2
        assert result.pattern_count == 2
        assert result.total_monthly_recurring == Decimal("25.98")

    def test_analyze_patterns_amount_variance_within_threshold(self):
        transactions = [
            self.create_transaction(
                normalized_description="utilities",
                amount=Decimal("100.00"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="utilities",
                amount=Decimal("105.00"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="utilities",
                amount=Decimal("110.00"),
                transaction_date=date(2024, 3, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 1
        pattern = result.patterns[0]
        assert pattern.normalized_description == "utilities"
        assert pattern.amount_variance < 0.15

    def test_analyze_patterns_amount_variance_exceeds_threshold(self):
        transactions = [
            self.create_transaction(
                normalized_description="utilities",
                amount=Decimal("100.00"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="utilities",
                amount=Decimal("100.00"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="utilities",
                amount=Decimal("200.00"),
                transaction_date=date(2024, 3, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 0

    def test_analyze_patterns_interval_not_monthly(self):
        transactions = [
            self.create_transaction(
                normalized_description="weekly expense",
                amount=Decimal("50.00"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="weekly expense",
                amount=Decimal("50.00"),
                transaction_date=date(2024, 1, 8),
            ),
            self.create_transaction(
                normalized_description="weekly expense",
                amount=Decimal("50.00"),
                transaction_date=date(2024, 1, 15),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 0

    def test_analyze_patterns_with_category(self):
        category_id = uuid.uuid4()
        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 1),
                category_id=category_id,
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
                category_id=category_id,
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 1),
                category_id=category_id,
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 1
        pattern = result.patterns[0]
        assert pattern.category_id == category_id

    def test_same_description_different_categories_are_separate_patterns(self):
        category_1 = uuid.uuid4()
        category_2 = uuid.uuid4()
        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 1),
                category_id=category_1,
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
                category_id=category_1,
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 1),
                category_id=category_1,
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 15),
                category_id=category_2,
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 15),
                category_id=category_2,
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 15),
                category_id=category_2,
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 2
        categories = {p.category_id for p in result.patterns}
        assert categories == {category_1, category_2}

    def test_analyze_patterns_calculates_annual_cost(self):
        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 1
        pattern = result.patterns[0]
        assert pattern.total_annual_cost == Decimal("9.99") * Decimal("12")

    def test_analyze_patterns_tracks_first_and_last_dates(self):
        first_date = date(2024, 1, 1)
        last_date = date(2024, 3, 1)

        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=first_date,
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=last_date,
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 1
        pattern = result.patterns[0]
        assert pattern.first_transaction_date == first_date
        assert pattern.last_transaction_date == last_date

    def test_analyze_patterns_tolerates_slight_timing_variations(self):
        transactions = [
            self.create_transaction(
                normalized_description="rent",
                amount=Decimal("1000.00"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="rent",
                amount=Decimal("1000.00"),
                transaction_date=date(2024, 2, 3),
            ),
            self.create_transaction(
                normalized_description="rent",
                amount=Decimal("1000.00"),
                transaction_date=date(2024, 3, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 1

    def test_different_descriptions_not_grouped(self):
        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="netflix",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="youtube premium",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 0

    def test_active_only_filters_old_patterns(self):
        today = date.today()
        old_date = today - timedelta(days=ACTIVE_PATTERNS_DAYS + 30)

        transactions = [
            self.create_transaction(
                normalized_description="cancelled subscription",
                amount=Decimal("9.99"),
                transaction_date=old_date - timedelta(days=60),
            ),
            self.create_transaction(
                normalized_description="cancelled subscription",
                amount=Decimal("9.99"),
                transaction_date=old_date - timedelta(days=30),
            ),
            self.create_transaction(
                normalized_description="cancelled subscription",
                amount=Decimal("9.99"),
                transaction_date=old_date,
            ),
        ]

        result_all = self.analyzer.analyze_patterns(transactions, self.user_id, active_only=False)
        result_active = self.analyzer.analyze_patterns(transactions, self.user_id, active_only=True)

        assert len(result_all.patterns) == 1
        assert len(result_active.patterns) == 0

    def test_active_only_keeps_recent_patterns(self):
        today = date.today()

        transactions = [
            self.create_transaction(
                normalized_description="active subscription",
                amount=Decimal("9.99"),
                transaction_date=today - timedelta(days=90),
            ),
            self.create_transaction(
                normalized_description="active subscription",
                amount=Decimal("9.99"),
                transaction_date=today - timedelta(days=60),
            ),
            self.create_transaction(
                normalized_description="active subscription",
                amount=Decimal("9.99"),
                transaction_date=today - timedelta(days=30),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id, active_only=True)

        assert len(result.patterns) == 1
        assert result.patterns[0].normalized_description == "active subscription"

    def test_active_only_with_mixed_patterns(self):
        cancelled_dates = [date(2024, 1, 15), date(2024, 2, 15), date(2024, 3, 15)]
        active_dates = [date(2025, 10, 15), date(2025, 11, 15), date(2025, 12, 15)]

        transactions = [
            self.create_transaction(
                normalized_description="cancelled subscription",
                amount=Decimal("9.99"),
                transaction_date=cancelled_dates[0],
            ),
            self.create_transaction(
                normalized_description="cancelled subscription",
                amount=Decimal("9.99"),
                transaction_date=cancelled_dates[1],
            ),
            self.create_transaction(
                normalized_description="cancelled subscription",
                amount=Decimal("9.99"),
                transaction_date=cancelled_dates[2],
            ),
            self.create_transaction(
                normalized_description="active subscription",
                amount=Decimal("15.99"),
                transaction_date=active_dates[0],
            ),
            self.create_transaction(
                normalized_description="active subscription",
                amount=Decimal("15.99"),
                transaction_date=active_dates[1],
            ),
            self.create_transaction(
                normalized_description="active subscription",
                amount=Decimal("15.99"),
                transaction_date=active_dates[2],
            ),
        ]

        result_all = self.analyzer.analyze_patterns(transactions, self.user_id, active_only=False)
        result_active = self.analyzer.analyze_patterns(transactions, self.user_id, active_only=True)

        assert len(result_all.patterns) == 2
        assert result_all.total_monthly_recurring == Decimal("25.98")

        assert len(result_active.patterns) == 1
        assert result_active.patterns[0].normalized_description == "active subscription"
        assert result_active.total_monthly_recurring == Decimal("15.99")

    def test_yearly_pattern_detected_with_three_occurrences(self):
        transactions = [
            self.create_transaction(
                normalized_description="annual insurance",
                amount=Decimal("500.00"),
                transaction_date=date(2022, 1, 15),
            ),
            self.create_transaction(
                normalized_description="annual insurance",
                amount=Decimal("500.00"),
                transaction_date=date(2023, 1, 15),
            ),
            self.create_transaction(
                normalized_description="annual insurance",
                amount=Decimal("500.00"),
                transaction_date=date(2024, 1, 15),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        yearly_patterns = [p for p in result.patterns if p.pattern_type == "yearly"]
        assert len(yearly_patterns) == 1
        pattern = yearly_patterns[0]
        assert pattern.normalized_description == "annual insurance"
        assert pattern.transaction_count == 3
        assert pattern.average_amount == Decimal("500.00")
        assert 360 <= pattern.interval_days <= 370

    def test_yearly_pattern_detected_with_two_occurrences(self):
        transactions = [
            self.create_transaction(
                normalized_description="annual insurance",
                amount=Decimal("500.00"),
                transaction_date=date(2023, 1, 15),
            ),
            self.create_transaction(
                normalized_description="annual insurance",
                amount=Decimal("500.00"),
                transaction_date=date(2024, 1, 15),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        yearly_patterns = [p for p in result.patterns if p.pattern_type == "yearly"]
        assert len(yearly_patterns) == 1

    def test_yearly_pattern_accepts_350_to_380_day_interval(self):
        transactions = [
            self.create_transaction(
                normalized_description="yearly subscription",
                amount=Decimal("99.99"),
                transaction_date=date(2022, 1, 1),
            ),
            self.create_transaction(
                normalized_description="yearly subscription",
                amount=Decimal("99.99"),
                transaction_date=date(2022, 12, 20),
            ),
            self.create_transaction(
                normalized_description="yearly subscription",
                amount=Decimal("99.99"),
                transaction_date=date(2023, 12, 8),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        yearly_patterns = [p for p in result.patterns if p.pattern_type == "yearly"]
        assert len(yearly_patterns) == 1

    def test_yearly_pattern_rejected_outside_interval(self):
        transactions = [
            self.create_transaction(
                normalized_description="nine_monthly payment",
                amount=Decimal("200.00"),
                transaction_date=date(2022, 1, 1),
            ),
            self.create_transaction(
                normalized_description="nine_monthly payment",
                amount=Decimal("200.00"),
                transaction_date=date(2022, 10, 1),
            ),
            self.create_transaction(
                normalized_description="nine_monthly payment",
                amount=Decimal("200.00"),
                transaction_date=date(2023, 7, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        yearly_patterns = [p for p in result.patterns if p.pattern_type == "yearly"]
        assert len(yearly_patterns) == 0

    def test_yearly_pattern_allows_10_percent_variance(self):
        transactions = [
            self.create_transaction(
                normalized_description="annual membership",
                amount=Decimal("100.00"),
                transaction_date=date(2022, 1, 15),
            ),
            self.create_transaction(
                normalized_description="annual membership",
                amount=Decimal("105.00"),
                transaction_date=date(2023, 1, 15),
            ),
            self.create_transaction(
                normalized_description="annual membership",
                amount=Decimal("109.00"),
                transaction_date=date(2024, 1, 15),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        yearly_patterns = [p for p in result.patterns if p.pattern_type == "yearly"]
        assert len(yearly_patterns) == 1

    def test_yearly_pattern_rejects_over_10_percent_variance(self):
        transactions = [
            self.create_transaction(
                normalized_description="variable annual fee",
                amount=Decimal("100.00"),
                transaction_date=date(2022, 1, 15),
            ),
            self.create_transaction(
                normalized_description="variable annual fee",
                amount=Decimal("100.00"),
                transaction_date=date(2023, 1, 15),
            ),
            self.create_transaction(
                normalized_description="variable annual fee",
                amount=Decimal("130.00"),
                transaction_date=date(2024, 1, 15),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        yearly_patterns = [p for p in result.patterns if p.pattern_type == "yearly"]
        assert len(yearly_patterns) == 0

    def test_mixed_monthly_and_yearly_patterns_detected(self):
        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 1),
            ),
            self.create_transaction(
                normalized_description="annual insurance",
                amount=Decimal("500.00"),
                transaction_date=date(2022, 3, 15),
            ),
            self.create_transaction(
                normalized_description="annual insurance",
                amount=Decimal("500.00"),
                transaction_date=date(2023, 3, 15),
            ),
            self.create_transaction(
                normalized_description="annual insurance",
                amount=Decimal("500.00"),
                transaction_date=date(2024, 3, 15),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        monthly_patterns = [p for p in result.patterns if p.pattern_type == "monthly"]
        yearly_patterns = [p for p in result.patterns if p.pattern_type == "yearly"]

        assert len(monthly_patterns) == 1
        assert len(yearly_patterns) == 1
        assert result.monthly_pattern_count == 1
        assert result.yearly_pattern_count == 1
        assert result.total_monthly_recurring == Decimal("9.99")
        assert result.total_yearly_recurring == Decimal("500.00")

    def test_yearly_pattern_annual_cost_equals_amount(self):
        transactions = [
            self.create_transaction(
                normalized_description="annual subscription",
                amount=Decimal("120.00"),
                transaction_date=date(2022, 6, 1),
            ),
            self.create_transaction(
                normalized_description="annual subscription",
                amount=Decimal("120.00"),
                transaction_date=date(2023, 6, 1),
            ),
            self.create_transaction(
                normalized_description="annual subscription",
                amount=Decimal("120.00"),
                transaction_date=date(2024, 6, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        yearly_patterns = [p for p in result.patterns if p.pattern_type == "yearly"]
        assert len(yearly_patterns) == 1
        pattern = yearly_patterns[0]
        assert pattern.total_annual_cost == Decimal("120.00")

    def test_monthly_pattern_type_is_set(self):
        transactions = [
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 2, 1),
            ),
            self.create_transaction(
                normalized_description="spotify",
                amount=Decimal("9.99"),
                transaction_date=date(2024, 3, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        assert len(result.patterns) == 1
        assert result.patterns[0].pattern_type == "monthly"

    def test_quarterly_pattern_detected(self):
        transactions = [
            self.create_transaction(
                normalized_description="quarterly membership",
                amount=Decimal("50.00"),
                transaction_date=date(2024, 1, 15),
            ),
            self.create_transaction(
                normalized_description="quarterly membership",
                amount=Decimal("50.00"),
                transaction_date=date(2024, 4, 15),
            ),
            self.create_transaction(
                normalized_description="quarterly membership",
                amount=Decimal("50.00"),
                transaction_date=date(2024, 7, 15),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        quarterly_patterns = [p for p in result.patterns if p.pattern_type == "quarterly"]
        assert len(quarterly_patterns) == 1
        pattern = quarterly_patterns[0]
        assert pattern.normalized_description == "quarterly membership"
        assert pattern.transaction_count == 3
        assert 85 <= pattern.interval_days <= 95
        assert result.quarterly_pattern_count == 1
        assert result.total_quarterly_recurring == Decimal("50.00")

    def test_quarterly_pattern_annual_cost_multiplied_by_4(self):
        transactions = [
            self.create_transaction(
                normalized_description="quarterly fee",
                amount=Decimal("25.00"),
                transaction_date=date(2024, 1, 1),
            ),
            self.create_transaction(
                normalized_description="quarterly fee",
                amount=Decimal("25.00"),
                transaction_date=date(2024, 4, 1),
            ),
            self.create_transaction(
                normalized_description="quarterly fee",
                amount=Decimal("25.00"),
                transaction_date=date(2024, 7, 1),
            ),
        ]

        result = self.analyzer.analyze_patterns(transactions, self.user_id)

        quarterly_patterns = [p for p in result.patterns if p.pattern_type == "quarterly"]
        assert len(quarterly_patterns) == 1
        pattern = quarterly_patterns[0]
        assert pattern.total_annual_cost == Decimal("100.00")
