from datetime import date
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models.initial_balance import InitialBalance
from app.ports.repositories.initial_balance import InitialBalanceRepository


class SQLAlchemyInitialBalanceRepository(InitialBalanceRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, initial_balance: InitialBalance) -> InitialBalance:
        self.db_session.add(initial_balance)
        self.db_session.commit()
        self.db_session.refresh(initial_balance)
        return initial_balance

    def get_by_id(self, initial_balance_id: UUID) -> Optional[InitialBalance]:
        return self.db_session.query(InitialBalance).filter(InitialBalance.id == initial_balance_id).first()

    def get_by_account_id_and_date(self, account_id: UUID, balance_date: date) -> Optional[InitialBalance]:
        return (
            self.db_session.query(InitialBalance)
            .filter(
                InitialBalance.account_id == account_id,
                InitialBalance.balance_date == balance_date,
            )
            .first()
        )

    def get_latest_by_account_id(self, account_id: UUID) -> Optional[InitialBalance]:
        return (
            self.db_session.query(InitialBalance)
            .filter(InitialBalance.account_id == account_id)
            .order_by(InitialBalance.balance_date.desc())
            .first()
        )

    def get_latest_by_account_id_and_date(self, account_id: UUID, before_date: date) -> Optional[InitialBalance]:
        """Get the latest initial balance for an account before a specific date"""
        return (
            self.db_session.query(InitialBalance)
            .filter(
                InitialBalance.account_id == account_id,
                InitialBalance.balance_date <= before_date,
            )
            .order_by(InitialBalance.balance_date.desc())
            .first()
        )

    def get_all_by_account_id(self, account_id: UUID) -> List[InitialBalance]:
        return (
            self.db_session.query(InitialBalance)
            .filter(InitialBalance.account_id == account_id)
            .order_by(InitialBalance.balance_date.desc())
            .all()
        )

    def get_latest_by_account_ids(self, account_ids: List[UUID]) -> Dict[UUID, InitialBalance]:
        if not account_ids:
            return {}

        latest_dates_subquery = (
            self.db_session.query(
                InitialBalance.account_id,
                func.max(InitialBalance.balance_date).label("max_date"),
            )
            .filter(InitialBalance.account_id.in_(account_ids))
            .group_by(InitialBalance.account_id)
            .subquery()
        )

        balances = (
            self.db_session.query(InitialBalance)
            .join(
                latest_dates_subquery,
                (InitialBalance.account_id == latest_dates_subquery.c.account_id)
                & (InitialBalance.balance_date == latest_dates_subquery.c.max_date),
            )
            .all()
        )

        return {balance.account_id: balance for balance in balances}

    def update(self, initial_balance: InitialBalance) -> InitialBalance:
        self.db_session.commit()
        self.db_session.refresh(initial_balance)
        return initial_balance

    def delete(self, initial_balance_id: UUID) -> bool:
        initial_balance = self.db_session.query(InitialBalance).filter(InitialBalance.id == initial_balance_id).first()
        if initial_balance:
            self.db_session.delete(initial_balance)
            self.db_session.commit()
            return True
        return False
