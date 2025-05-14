from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.source import Source


class SourceRepository(ABC):
    @abstractmethod
    def create(self, source: Source) -> Source:
        pass

    @abstractmethod
    def get_by_id(self, source_id: UUID) -> Optional[Source]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Source]:
        pass

    @abstractmethod
    def get_all(self) -> List[Source]:
        pass

    @abstractmethod
    def update(self, source: Source) -> Source:
        pass

    @abstractmethod
    def delete(self, source_id: UUID) -> None:
        pass
