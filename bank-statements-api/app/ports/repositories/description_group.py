from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.description_group import DescriptionGroup


class DescriptionGroupRepository(ABC):
    @abstractmethod
    def create(self, group: DescriptionGroup) -> DescriptionGroup:
        pass

    @abstractmethod
    def get_by_id(self, group_id: UUID) -> Optional[DescriptionGroup]:
        pass

    @abstractmethod
    def get_all(self) -> List[DescriptionGroup]:
        pass

    @abstractmethod
    def update(self, group: DescriptionGroup) -> DescriptionGroup:
        pass

    @abstractmethod
    def delete(self, group_id: UUID) -> None:
        pass

    @abstractmethod
    def get_by_normalized_description(self, normalized_description: str) -> Optional[DescriptionGroup]:
        pass

    @abstractmethod
    def get_description_to_group_map(self) -> Dict[str, UUID]:
        pass
