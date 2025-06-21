import csv
import io
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

    def upsert_accounts_from_csv(self, csv_content: str) -> List[Account]:
        """
        Upsert accounts from CSV content.
        Expected CSV format: name
        """
        accounts = []
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        for row in csv_reader:
            if "name" not in row:
                raise ValueError("CSV must contain 'name' column")

            name = row["name"].strip()
            if not name:
                continue

            # Check if account already exists
            existing_account = self.account_repository.get_by_name(name)
            if existing_account:
                accounts.append(existing_account)
            else:
                # Create new account
                new_account = Account(name=name)
                created_account = self.account_repository.create(new_account)
                accounts.append(created_account)

        return accounts
