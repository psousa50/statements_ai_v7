from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.saved_filter import SavedFilter
from app.ports.repositories.saved_filter import SavedFilterRepository


class SQLAlchemySavedFilterRepository(SavedFilterRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, user_id: UUID, filter_data: dict) -> SavedFilter:
        saved_filter = SavedFilter(
            user_id=user_id,
            filter_data=filter_data,
        )
        self.db_session.add(saved_filter)
        self.db_session.commit()
        self.db_session.refresh(saved_filter)
        return saved_filter

    def get_by_id(self, filter_id: UUID, user_id: UUID) -> Optional[SavedFilter]:
        now = datetime.now(timezone.utc)
        return (
            self.db_session.query(SavedFilter)
            .filter(
                SavedFilter.id == filter_id,
                SavedFilter.user_id == user_id,
                SavedFilter.expires_at > now,
            )
            .first()
        )

    def delete_expired(self, user_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        result = (
            self.db_session.query(SavedFilter)
            .filter(
                SavedFilter.user_id == user_id,
                SavedFilter.expires_at <= now,
            )
            .delete()
        )
        self.db_session.commit()
        return result
