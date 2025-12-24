from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.models.saved_filter import SavedFilter


class SavedFilterRepository(ABC):
    @abstractmethod
    def create(self, user_id: UUID, filter_data: dict) -> SavedFilter:
        pass

    @abstractmethod
    def get_by_id(self, filter_id: UUID, user_id: UUID) -> Optional[SavedFilter]:
        pass

    @abstractmethod
    def delete_expired(self, user_id: UUID) -> int:
        pass
