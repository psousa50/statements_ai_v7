from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import List, Optional
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
    def get_by_source_and_date(self, source_id: UUID, balance_date: date) -> Optional[InitialBalance]:
        """Get initial balance by source ID and date"""
        pass

    @abstractmethod
    def get_latest_by_source(self, source_id: UUID) -> Optional[InitialBalance]:
        """Get the latest initial balance for a source"""
        pass

    @abstractmethod
    def get_latest_by_source_and_date(self, source_id: UUID, before_date: date) -> Optional[InitialBalance]:
        """Get the latest initial balance for a source before a specific date"""
        pass

    @abstractmethod
    def get_all_by_source(self, source_id: UUID) -> List[InitialBalance]:
        """Get all initial balances for a source"""
        pass

    @abstractmethod
    def update(self, initial_balance: InitialBalance) -> InitialBalance:
        """Update an initial balance"""
        pass

    @abstractmethod
    def delete(self, initial_balance_id: UUID) -> bool:
        """Delete an initial balance"""
        pass
