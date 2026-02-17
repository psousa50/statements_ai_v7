from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.tag import Tag


class TagRepository(ABC):
    @abstractmethod
    def create(self, tag: Tag) -> Tag:
        pass

    @abstractmethod
    def get_by_id(self, tag_id: UUID, user_id: UUID) -> Optional[Tag]:
        pass

    @abstractmethod
    def get_all(self, user_id: UUID) -> List[Tag]:
        pass

    @abstractmethod
    def get_by_name_ci(self, name: str, user_id: UUID) -> Optional[Tag]:
        pass

    @abstractmethod
    def delete(self, tag_id: UUID, user_id: UUID) -> bool:
        pass

    @abstractmethod
    def add_to_transaction(self, transaction_id: UUID, tag_id: UUID) -> None:
        pass

    @abstractmethod
    def remove_from_transaction(self, transaction_id: UUID, tag_id: UUID) -> None:
        pass

    @abstractmethod
    def has_transactions(self, tag_id: UUID) -> bool:
        pass

    @abstractmethod
    def bulk_add_to_transactions(self, transaction_ids: List[UUID], tag_id: UUID) -> int:
        pass
