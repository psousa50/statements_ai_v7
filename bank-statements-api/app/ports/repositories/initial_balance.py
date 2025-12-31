from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.initial_balance import InitialBalance


class InitialBalanceRepository(ABC):
    @abstractmethod
    def create(self, initial_balance: InitialBalance) -> InitialBalance:
        """Create a new initial balance"""
        pass

    @abstractmethod
    def get_by_id(self, initial_balance_id: UUID) -> Optional[InitialBalance]:
        """Get an initial balance by ID"""
        pass

    @abstractmethod
    def get_by_account_id_and_date(self, account_id: UUID, balance_date: date) -> Optional[InitialBalance]:
        """Get initial balance by source ID and date"""
        pass

    @abstractmethod
    def get_latest_by_account_id(self, account_id: UUID) -> Optional[InitialBalance]:
        """Get the latest initial balance for a source"""
        pass

    @abstractmethod
    def get_latest_by_account_id_and_date(self, account_id: UUID, before_date: date) -> Optional[InitialBalance]:
        """Get the latest initial balance for a source before a specific date"""
        pass

    @abstractmethod
    def get_all_by_account_id(self, account_id: UUID) -> List[InitialBalance]:
        """Get all initial balances for a source"""
        pass

    @abstractmethod
    def get_latest_by_account_ids(self, account_ids: List[UUID]) -> Dict[UUID, InitialBalance]:
        """Get the latest initial balance for multiple accounts in a single query"""
        pass

    @abstractmethod
    def update(self, initial_balance: InitialBalance) -> InitialBalance:
        """Update an initial balance"""
        pass

    @abstractmethod
    def delete(self, initial_balance_id: UUID) -> bool:
        """Delete an initial balance"""
        pass
