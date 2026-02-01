from datetime import date
from decimal import Decimal
from typing import Any, Callable, Optional
from uuid import UUID

from app.services.account import AccountService
from app.services.category import CategoryService
from app.services.recurring_expense_analyzer import RecurringExpenseAnalyzer
from app.services.transaction import TransactionService


def create_chat_functions(
    user_id: UUID,
    transaction_service: TransactionService,
    category_service: CategoryService,
    account_service: AccountService,
    recurring_analyzer: RecurringExpenseAnalyzer,
) -> list[Callable]:

    async def get_category_totals(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        transaction_type: str = "debit",
    ) -> dict[str, Any]:
        """Get spending totals grouped by category. Returns ALL transactions unless dates specified.

        Args:
            start_date: Optional start date (YYYY-MM-DD). Omit to include all history.
            end_date: Optional end date (YYYY-MM-DD). Omit to include all history.
            transaction_type: One of 'debit', 'credit', or 'all'

        IMPORTANT: Do NOT pass dates unless the user specifically asks for a time period.
        """
        parsed_start = date.fromisoformat(start_date) if start_date else None
        parsed_end = date.fromisoformat(end_date) if end_date else None

        totals = transaction_service.get_category_totals(
            user_id=user_id,
            start_date=parsed_start,
            end_date=parsed_end,
            exclude_transfers=True,
            transaction_type=transaction_type,
        )

        categories = category_service.get_all_categories(user_id)
        category_map = {c.id: c for c in categories}

        result = []
        for cat_id, data in totals.items():
            cat = category_map.get(cat_id) if cat_id else None
            cat_name = cat.name if cat else "Uncategorised"
            parent_name = None
            if cat and cat.parent_id:
                parent = category_map.get(cat.parent_id)
                parent_name = parent.name if parent else None

            result.append(
                {
                    "category": cat_name,
                    "parent_category": parent_name,
                    "total_amount": float(data.get("total_amount", Decimal("0"))),
                    "transaction_count": int(data.get("count", 0)),
                }
            )

        result.sort(key=lambda x: x["total_amount"])
        return {"category_totals": result[:20]}

    async def get_transactions(
        description_search: Optional[str] = None,
        category_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search transactions with filters. Returns recent transactions unless dates specified.

        Args:
            description_search: Text to search in transaction descriptions
            category_name: Filter by category name
            start_date: Optional start date (YYYY-MM-DD). Omit to include all history.
            end_date: Optional end date (YYYY-MM-DD). Omit to include all history.
            min_amount: Minimum transaction amount
            max_amount: Maximum transaction amount
            limit: Maximum number of results (default 20, max 50)

        IMPORTANT: Do NOT pass dates unless the user specifically asks for a time period.
        """
        parsed_start = date.fromisoformat(start_date) if start_date else None
        parsed_end = date.fromisoformat(end_date) if end_date else None
        limit = min(limit, 50)

        category_ids = None
        if category_name:
            categories = category_service.get_all_categories(user_id)
            matching = [c for c in categories if c.name.lower() == category_name.lower()]
            if matching:
                category_ids = [matching[0].id]

        response = transaction_service.get_transactions_paginated(
            user_id=user_id,
            page=1,
            page_size=limit,
            description_search=description_search,
            category_ids=category_ids,
            start_date=parsed_start,
            end_date=parsed_end,
            min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
            max_amount=Decimal(str(max_amount)) if max_amount is not None else None,
            exclude_transfers=True,
            sort_field="date",
            sort_direction="desc",
        )

        categories = category_service.get_all_categories(user_id)
        category_map = {c.id: c.name for c in categories}

        transactions = []
        for t in response.transactions:
            transactions.append(
                {
                    "date": t.date.isoformat(),
                    "description": t.description,
                    "amount": float(t.amount),
                    "category": category_map.get(t.category_id, "Uncategorised"),
                }
            )

        return {
            "transactions": transactions,
            "total_count": response.total,
            "total_amount": float(response.total_amount) if response.total_amount else 0,
        }

    async def get_recurring_patterns(
        pattern_type: Optional[str] = None,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """Get recurring expenses and subscriptions.

        Args:
            pattern_type: Filter by pattern type: 'monthly', 'quarterly', or 'yearly'
            active_only: Only show patterns with recent transactions (default True)
        """
        from datetime import timedelta

        cutoff_date = date.today() - timedelta(days=36 * 30)
        response = transaction_service.get_transactions_paginated(
            user_id=user_id,
            page=1,
            page_size=5000,
            start_date=cutoff_date,
            exclude_transfers=True,
            transaction_type="debit",
        )

        analysis = recurring_analyzer.analyze_patterns(
            transactions=response.transactions,  # type: ignore[arg-type]
            user_id=user_id,
            active_only=active_only,
        )

        patterns = analysis.patterns
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]

        categories = category_service.get_all_categories(user_id)
        category_map = {c.id: c.name for c in categories}

        result = []
        for p in patterns[:20]:
            result.append(
                {
                    "description": p.description,
                    "pattern_type": p.pattern_type,
                    "average_amount": float(p.average_amount),
                    "transaction_count": p.transaction_count,
                    "category": category_map.get(p.category_id, "Uncategorised"),
                    "annual_cost": float(p.total_annual_cost),
                }
            )

        return {
            "patterns": result,
            "summary": {
                "monthly_total": float(analysis.total_monthly_recurring),
                "quarterly_total": float(analysis.total_quarterly_recurring),
                "yearly_total": float(analysis.total_yearly_recurring),
            },
        }

    async def get_time_series(
        period: str = "month",
        category_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get spending over time for trend analysis.

        Args:
            period: Aggregation period: 'month' or 'week'
            category_name: Optional category name to filter
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
        """
        parsed_start = date.fromisoformat(start_date) if start_date else None
        parsed_end = date.fromisoformat(end_date) if end_date else None

        category_id = None
        if category_name:
            categories = category_service.get_all_categories(user_id)
            matching = [c for c in categories if c.name.lower() == category_name.lower()]
            if matching:
                category_id = matching[0].id

        data_points = transaction_service.get_category_time_series(
            user_id=user_id,
            category_id=category_id,
            period=period,
            start_date=parsed_start,
            end_date=parsed_end,
            exclude_transfers=True,
            transaction_type="debit",
        )

        result = []
        for point in data_points:
            result.append(
                {
                    "period": point.get("period"),
                    "total_amount": float(point.get("total_amount", 0)),
                    "transaction_count": point.get("transaction_count", 0),
                }
            )

        return {"time_series": result, "period_type": period}

    async def get_categories() -> dict[str, Any]:
        """List all available spending categories."""
        categories = category_service.get_all_categories(user_id)

        result = []
        for cat in categories:
            parent_name = None
            if cat.parent_id:
                parent = next((c for c in categories if c.id == cat.parent_id), None)
                parent_name = parent.name if parent else None

            result.append(
                {
                    "name": cat.name,
                    "parent": parent_name,
                }
            )

        return {"categories": result}

    async def get_accounts() -> dict[str, Any]:
        """List user's bank accounts."""
        accounts = account_service.get_all_accounts(user_id)

        result = []
        for acc in accounts:
            result.append(
                {
                    "name": acc.name,
                    "currency": acc.currency,
                }
            )

        return {"accounts": result}

    return [
        get_category_totals,
        get_transactions,
        get_recurring_patterns,
        get_time_series,
        get_categories,
        get_accounts,
    ]
