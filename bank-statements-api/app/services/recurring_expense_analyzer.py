from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.transaction import Transaction
from app.ports.repositories.description_group import DescriptionGroupRepository


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
        amount_variance_threshold: float = 0.15,
    ):
        self.description_group_repository = description_group_repository
        self.min_occurrences = min_occurrences
        self.amount_variance_threshold = amount_variance_threshold

    def analyze_patterns(self, transactions: List[Transaction]) -> RecurringAnalysisResult:
        monthly_patterns = self._find_monthly_patterns(transactions)

        if self.description_group_repository:
            patterns = self._merge_grouped_patterns(monthly_patterns)
        else:
            patterns = monthly_patterns

        total_monthly = sum(p.average_amount for p in patterns)

        return RecurringAnalysisResult(
            patterns=patterns,
            total_monthly_recurring=total_monthly,
            pattern_count=len(patterns),
        )

    def _find_monthly_patterns(self, transactions: List[Transaction]) -> List[RecurringPattern]:
        groups = self._group_by_normalized_description(transactions)
        patterns = []

        for normalized_description, group_transactions in groups.items():
            if len(group_transactions) < self.min_occurrences:
                continue

            sorted_transactions = sorted(group_transactions, key=lambda t: t.date)

            intervals = self._calculate_intervals(sorted_transactions)
            if not intervals:
                continue

            avg_interval = sum(intervals) / len(intervals)

            if not self._is_monthly_interval(avg_interval):
                continue

            amounts = [abs(t.amount) for t in sorted_transactions]
            avg_amount = sum(amounts) / len(amounts)

            if avg_amount == 0:
                continue

            variance = max(abs(a - avg_amount) / avg_amount for a in amounts)

            if variance <= self.amount_variance_threshold:
                category_id = next((t.category_id for t in sorted_transactions if t.category_id), None)
                description = sorted_transactions[0].description

                annual_cost = avg_amount * Decimal("12")

                pattern = RecurringPattern(
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
                patterns.append(pattern)

        return patterns

    def _group_by_normalized_description(self, transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
        groups = defaultdict(list)
        for transaction in transactions:
            groups[transaction.normalized_description].append(transaction)
        return groups

    def _calculate_intervals(self, sorted_transactions: List[Transaction]) -> List[float]:
        intervals = []
        for i in range(1, len(sorted_transactions)):
            days = (sorted_transactions[i].date - sorted_transactions[i - 1].date).days
            intervals.append(float(days))
        return intervals

    def _is_monthly_interval(self, avg_interval: float) -> bool:
        return 25 <= avg_interval <= 35

    def _merge_grouped_patterns(self, patterns: List[RecurringPattern]) -> List[RecurringPattern]:
        description_to_group = self.description_group_repository.get_description_to_group_map()

        grouped_patterns = defaultdict(list)

        for pattern in patterns:
            group_id = description_to_group.get(pattern.normalized_description, pattern.normalized_description)
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
