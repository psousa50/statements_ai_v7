from typing import List, Optional
from uuid import UUID

from app.domain.models.account import Account
from app.ports.repositories.account import AccountRepository


class AccountService:
    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository

    def create_account(self, name: str) -> Account:
        account = Account(name=name)
        return self.account_repository.create(account)

    def get_account_by_id(self, account_id: UUID) -> Optional[Account]:
        return self.account_repository.get_by_id(account_id)

    def get_account_by_name(self, name: str) -> Optional[Account]:
        return self.account_repository.get_by_name(name)

    def get_all_accounts(self) -> List[Account]:
        return self.account_repository.get_all()

    def update_account(self, account_id: UUID, name: str) -> Optional[Account]:
        account = self.account_repository.get_by_id(account_id)
        if account:
            account.name = name
            return self.account_repository.update(account)
        return None

    def delete_account(self, account_id: UUID) -> bool:
        account = self.account_repository.get_by_id(account_id)
        if account:
            self.account_repository.delete(account_id)
            return True
        return False
