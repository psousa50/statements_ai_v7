from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.transaction import Transaction
from app.ports.repositories.description_group import DescriptionGroupRepository

ACTIVE_PATTERNS_DAYS = 90


@dataclass
class RecurringPattern:
    description: str
    normalized_description: str
    frequency: str
    interval_days: float
    average_amount: Decimal
    amount_variance: float
    transaction_count: int
    transactions: List[Transaction]
    category_id: Optional[UUID]
    first_transaction_date: date
    last_transaction_date: date
    total_annual_cost: Decimal

    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "normalized_description": self.normalized_description,
            "frequency": self.frequency,
            "interval_days": self.interval_days,
            "average_amount": float(self.average_amount),
            "amount_variance": self.amount_variance,
            "transaction_count": self.transaction_count,
            "transaction_ids": [str(t.id) for t in self.transactions],
            "category_id": str(self.category_id) if self.category_id else None,
            "first_transaction_date": self.first_transaction_date.isoformat(),
            "last_transaction_date": self.last_transaction_date.isoformat(),
            "total_annual_cost": float(self.total_annual_cost),
        }


@dataclass
class RecurringAnalysisResult:
    patterns: List[RecurringPattern]
    total_monthly_recurring: Decimal
    pattern_count: int

    def to_dict(self) -> Dict:
        return {
            "patterns": [p.to_dict() for p in self.patterns],
            "summary": {
                "total_monthly_recurring": float(self.total_monthly_recurring),
                "pattern_count": self.pattern_count,
            },
        }


class RecurringExpenseAnalyzer:
    def __init__(
        self,
        description_group_repository: Optional[DescriptionGroupRepository] = None,
        min_occurrences: int = 3,
        amount_variance_threshold: float = 0.99,
    ):
        self.description_group_repository = description_group_repository
        self.min_occurrences = min_occurrences
        self.amount_variance_threshold = amount_variance_threshold

    def analyze_patterns(
        self,
        transactions: List[Transaction],
        user_id: UUID,
        active_only: bool = False,
    ) -> RecurringAnalysisResult:
        monthly_patterns = self._find_monthly_patterns(transactions)

        if self.description_group_repository:
            patterns = self._merge_grouped_patterns(monthly_patterns, user_id)
        else:
            patterns = monthly_patterns

        if active_only:
            cutoff_date = date.today() - timedelta(days=ACTIVE_PATTERNS_DAYS)
            patterns = [p for p in patterns if p.last_transaction_date >= cutoff_date]

        total_monthly = sum(p.average_amount for p in patterns)

        return RecurringAnalysisResult(
            patterns=patterns,
            total_monthly_recurring=total_monthly,
            pattern_count=len(patterns),
        )

    def _find_monthly_patterns(self, transactions: List[Transaction]) -> List[RecurringPattern]:
        groups = self._group_by_normalized_description(transactions)
        patterns = []

        for (normalized_description, category_id), group_transactions in groups.items():
            if len(group_transactions) < self.min_occurrences:
                continue

            sorted_transactions = sorted(group_transactions, key=lambda t: t.date)
            monthly_transactions = self._filter_to_monthly_sequence(sorted_transactions)

            if len(monthly_transactions) < self.min_occurrences:
                continue

            intervals = self._calculate_intervals(monthly_transactions)
            if not intervals:
                continue

            avg_interval = sum(intervals) / len(intervals)

            first_date = sorted_transactions[0].date
            last_date = sorted_transactions[-1].date
            months_covered = (last_date.year - first_date.year) * 12 + (last_date.month - first_date.month) + 1

            total_amount = sum(abs(t.amount) for t in group_transactions)
            avg_amount = Decimal(total_amount) / Decimal(months_covered)

            if avg_amount == 0:
                continue

            amounts = [abs(t.amount) for t in group_transactions]
            avg_per_txn = total_amount / len(amounts)
            variance = max(abs(a - avg_per_txn) / avg_per_txn for a in amounts) if avg_per_txn > 0 else 0

            if variance <= self.amount_variance_threshold:
                description = monthly_transactions[0].description
                actual_normalized_description = monthly_transactions[0].normalized_description

                annual_cost = avg_amount * Decimal("12")

                pattern = RecurringPattern(
                    description=description,
                    normalized_description=actual_normalized_description,
                    frequency="monthly",
                    interval_days=avg_interval,
                    average_amount=avg_amount,
                    amount_variance=variance,
                    transaction_count=len(group_transactions),
                    transactions=group_transactions,
                    category_id=category_id,
                    first_transaction_date=sorted_transactions[0].date,
                    last_transaction_date=sorted_transactions[-1].date,
                    total_annual_cost=annual_cost,
                )
                patterns.append(pattern)

        return patterns

    def _group_by_normalized_description(
        self, transactions: List[Transaction]
    ) -> Dict[tuple, List[Transaction]]:
        groups = defaultdict(list)
        for transaction in transactions:
            key = (transaction.normalized_description, transaction.category_id)
            groups[key].append(transaction)
        return {k: v for k, v in groups.items() if len(v) >= self.min_occurrences}

    def _filter_to_monthly_sequence(self, sorted_transactions: List[Transaction]) -> List[Transaction]:
        if len(sorted_transactions) < 2:
            return sorted_transactions

        best_sequence: List[Transaction] = []

        for start_idx in range(len(sorted_transactions)):
            sequence = [sorted_transactions[start_idx]]

            for i in range(start_idx + 1, len(sorted_transactions)):
                days = (sorted_transactions[i].date - sequence[-1].date).days
                if 26 <= days <= 34:
                    sequence.append(sorted_transactions[i])

            if len(sequence) > len(best_sequence):
                best_sequence = sequence

        return best_sequence

    def _calculate_intervals(self, sorted_transactions: List[Transaction]) -> List[float]:
        intervals = []
        for i in range(1, len(sorted_transactions)):
            days = (sorted_transactions[i].date - sorted_transactions[i - 1].date).days
            intervals.append(float(days))
        return intervals

    def _is_monthly_interval(self, intervals: List[float]) -> bool:
        if not intervals:
            return False
        return all(26 <= interval <= 34 for interval in intervals)

    def _merge_grouped_patterns(self, patterns: List[RecurringPattern], user_id: UUID) -> List[RecurringPattern]:
        description_to_group = self.description_group_repository.get_description_to_group_map(user_id)

        grouped_patterns = defaultdict(list)

        for pattern in patterns:
            if pattern.normalized_description in description_to_group:
                group_id = description_to_group[pattern.normalized_description]
            else:
                group_id = (pattern.normalized_description, pattern.category_id)
            grouped_patterns[group_id].append(pattern)

        merged_patterns = []

        for group_id, pattern_list in grouped_patterns.items():
            if len(pattern_list) == 1:
                merged_patterns.append(pattern_list[0])
            else:
                merged_pattern = self._combine_patterns(pattern_list)
                merged_patterns.append(merged_pattern)

        return merged_patterns

    def _combine_patterns(self, patterns: List[RecurringPattern]) -> RecurringPattern:
        all_transactions = []
        for pattern in patterns:
            all_transactions.extend(pattern.transactions)

        sorted_transactions = sorted(all_transactions, key=lambda t: t.date)

        amounts = [abs(t.amount) for t in sorted_transactions]
        avg_amount = sum(amounts) / len(amounts)

        intervals = self._calculate_intervals(sorted_transactions)
        avg_interval = sum(intervals) / len(intervals) if intervals else 30.0

        variance = max(abs(a - avg_amount) / avg_amount for a in amounts) if avg_amount > 0 else 0

        category_id = next((t.category_id for t in sorted_transactions if t.category_id), None)

        description = sorted(patterns, key=lambda p: p.description)[0].description
        normalized_description = sorted(patterns, key=lambda p: p.normalized_description)[0].normalized_description

        annual_cost = avg_amount * Decimal("12")

        return RecurringPattern(
            description=description,
            normalized_description=normalized_description,
            frequency="monthly",
            interval_days=avg_interval,
            average_amount=avg_amount,
            amount_variance=variance,
            transaction_count=len(sorted_transactions),
            transactions=sorted_transactions,
            category_id=category_id,
            first_transaction_date=sorted_transactions[0].date,
            last_transaction_date=sorted_transactions[-1].date,
            total_annual_cost=annual_cost,
        )
