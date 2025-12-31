from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.initial_balance import InitialBalance
from app.ports.repositories.initial_balance import InitialBalanceRepository


class InitialBalanceService:
    def __init__(
        self,
        initial_balance_repository: InitialBalanceRepository,
    ):
        self.initial_balance_repository = initial_balance_repository

    def create_initial_balance(
        self,
        account_id: UUID,
        balance_date: date,
        balance_amount: Decimal,
    ) -> InitialBalance:
        """Create a new initial balance for a source"""
        initial_balance = InitialBalance(
            account_id=account_id,
            balance_date=balance_date,
            balance_amount=balance_amount,
        )
        return self.initial_balance_repository.create(initial_balance)

    def get_latest_balance(self, account_id: UUID) -> Optional[InitialBalance]:
        return self.initial_balance_repository.get_latest_by_account_id(account_id)

    def get_latest_balances_for_accounts(self, account_ids: List[UUID]) -> Dict[UUID, InitialBalance]:
        return self.initial_balance_repository.get_latest_by_account_ids(account_ids)

    def get_all_balances(self, account_id: UUID) -> List[InitialBalance]:
        """Get all initial balances for a source"""
        return self.initial_balance_repository.get_all_by_account_id(account_id)

    def get_balance_by_date(self, account_id: UUID, balance_date: date) -> Optional[InitialBalance]:
        """Get initial balance for a specific date"""
        return self.initial_balance_repository.get_by_account_id_and_date(account_id, balance_date)

    def update_initial_balance(
        self,
        initial_balance_id: UUID,
        balance_date: date,
        balance_amount: Decimal,
    ) -> Optional[InitialBalance]:
        """Update an existing initial balance"""
        initial_balance = self.initial_balance_repository.get_by_id(initial_balance_id)
        if initial_balance:
            initial_balance.balance_date = balance_date
            initial_balance.balance_amount = balance_amount
            return self.initial_balance_repository.update(initial_balance)
        return None

    def delete_initial_balance(self, initial_balance_id: UUID) -> bool:
        """Delete an initial balance"""
        return self.initial_balance_repository.delete(initial_balance_id)
