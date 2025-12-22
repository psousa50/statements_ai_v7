from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.account import Account


class AccountRepository(ABC):
    @abstractmethod
    def create(self, account: Account) -> Account:
        pass

    @abstractmethod
    def get_by_id(self, account_id: UUID, user_id: UUID) -> Optional[Account]:
        pass

    @abstractmethod
    def get_by_name(self, name: str, user_id: UUID) -> Optional[Account]:
        pass

    @abstractmethod
    def get_all(self, user_id: UUID) -> List[Account]:
        pass

    @abstractmethod
    def update(self, account: Account) -> Account:
        pass

    @abstractmethod
    def delete(self, account_id: UUID, user_id: UUID) -> None:
        pass
