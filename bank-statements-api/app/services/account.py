import csv
import io
from typing import List, Optional
from uuid import UUID

from app.domain.models.account import Account
from app.ports.repositories.account import AccountRepository


class AccountService:
    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository

    def create_account(self, name: str, user_id: UUID) -> Account:
        account = Account(name=name, user_id=user_id)
        return self.account_repository.create(account)

    def get_account(self, account_id: UUID, user_id: UUID) -> Optional[Account]:
        return self.account_repository.get_by_id(account_id, user_id)

    def get_account_by_name(self, name: str, user_id: UUID) -> Optional[Account]:
        return self.account_repository.get_by_name(name, user_id)

    def get_all_accounts(self, user_id: UUID) -> List[Account]:
        return self.account_repository.get_all(user_id)

    def update_account(self, account_id: UUID, name: str, user_id: UUID) -> Optional[Account]:
        account = self.account_repository.get_by_id(account_id, user_id)
        if account:
            account.name = name
            return self.account_repository.update(account)
        return None

    def delete_account(self, account_id: UUID, user_id: UUID) -> bool:
        account = self.account_repository.get_by_id(account_id, user_id)
        if account:
            self.account_repository.delete(account_id, user_id)
            return True
        return False

    def upsert_accounts_from_csv(self, csv_content: str, user_id: UUID) -> List[Account]:
        accounts = []
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        for row in csv_reader:
            if "name" not in row:
                raise ValueError("CSV must contain 'name' column")

            name = row["name"].strip()
            if not name:
                continue

            existing_account = self.account_repository.get_by_name(name, user_id)
            if existing_account:
                accounts.append(existing_account)
            else:
                new_account = Account(name=name, user_id=user_id)
                created_account = self.account_repository.create(new_account)
                accounts.append(created_account)

        return accounts
