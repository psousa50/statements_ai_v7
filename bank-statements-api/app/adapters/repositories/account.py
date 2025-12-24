from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.account import Account
from app.ports.repositories.account import AccountRepository


class SQLAlchemyAccountRepository(AccountRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, account: Account) -> Account:
        self.db_session.add(account)
        self.db_session.commit()
        self.db_session.refresh(account)
        return account

    def get_by_id(self, account_id: UUID, user_id: UUID) -> Optional[Account]:
        return self.db_session.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()

    def get_by_name(self, name: str, user_id: UUID) -> Optional[Account]:
        return self.db_session.query(Account).filter(Account.name == name, Account.user_id == user_id).first()

    def get_all(self, user_id: UUID) -> List[Account]:
        return self.db_session.query(Account).filter(Account.user_id == user_id).all()

    def update(self, account: Account) -> Account:
        self.db_session.commit()
        self.db_session.refresh(account)
        return account

    def delete(self, account_id: UUID, user_id: UUID) -> None:
        account = self.get_by_id(account_id, user_id)
        if account:
            self.db_session.delete(account)
            self.db_session.commit()
