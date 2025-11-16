from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.transaction import Transaction


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
    def __init__(self, min_occurrences: int = 3, amount_variance_threshold: float = 0.15):
        self.min_occurrences = min_occurrences
        self.amount_variance_threshold = amount_variance_threshold

    def analyze_patterns(self, transactions: List[Transaction]) -> RecurringAnalysisResult:
        patterns = []

        monthly_patterns = self._find_monthly_patterns(transactions)
        patterns.extend(monthly_patterns)

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
