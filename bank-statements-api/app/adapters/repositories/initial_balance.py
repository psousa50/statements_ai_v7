from datetime import date
from typing import List, Optional
from uuid import UUID

from app.domain.models.initial_balance import InitialBalance
from app.ports.repositories.initial_balance import InitialBalanceRepository
from sqlalchemy.orm import Session


class SQLAlchemyInitialBalanceRepository(InitialBalanceRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, initial_balance: InitialBalance) -> InitialBalance:
        self.db_session.add(initial_balance)
        self.db_session.commit()
        self.db_session.refresh(initial_balance)
        return initial_balance

    def get_by_id(self, initial_balance_id: UUID) -> Optional[InitialBalance]:
        return (
            self.db_session.query(InitialBalance)
            .filter(InitialBalance.id == initial_balance_id)
            .first()
        )

    def get_by_source_and_date(
        self, source_id: UUID, balance_date: date
    ) -> Optional[InitialBalance]:
        return (
            self.db_session.query(InitialBalance)
            .filter(
                InitialBalance.source_id == source_id,
                InitialBalance.balance_date == balance_date,
            )
            .first()
        )

    def get_latest_by_source(self, source_id: UUID) -> Optional[InitialBalance]:
        return (
            self.db_session.query(InitialBalance)
            .filter(InitialBalance.source_id == source_id)
            .order_by(InitialBalance.balance_date.desc())
            .first()
        )

    def get_latest_by_source_and_date(
        self, source_id: UUID, before_date: date
    ) -> Optional[InitialBalance]:
        """Get the latest initial balance for a source before a specific date"""
        return (
            self.db_session.query(InitialBalance)
            .filter(
                InitialBalance.source_id == source_id,
                InitialBalance.balance_date <= before_date,
            )
            .order_by(InitialBalance.balance_date.desc())
            .first()
        )

    def get_all_by_source(self, source_id: UUID) -> List[InitialBalance]:
        return (
            self.db_session.query(InitialBalance)
            .filter(InitialBalance.source_id == source_id)
            .order_by(InitialBalance.balance_date.desc())
            .all()
        )

    def update(self, initial_balance: InitialBalance) -> InitialBalance:
        self.db_session.commit()
        self.db_session.refresh(initial_balance)
        return initial_balance

    def delete(self, initial_balance_id: UUID) -> bool:
        initial_balance = (
            self.db_session.query(InitialBalance)
            .filter(InitialBalance.id == initial_balance_id)
            .first()
        )
        if initial_balance:
            self.db_session.delete(initial_balance)
            self.db_session.commit()
            return True
        return False
