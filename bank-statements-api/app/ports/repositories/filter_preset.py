from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.models.filter_preset import FilterPreset


class FilterPresetRepository(ABC):
    @abstractmethod
    def create(self, user_id: UUID, name: str, filter_data: dict) -> FilterPreset:
        pass

    @abstractmethod
    def get_all_by_user(self, user_id: UUID) -> list[FilterPreset]:
        pass

    @abstractmethod
    def get_by_id(self, preset_id: UUID, user_id: UUID) -> Optional[FilterPreset]:
        pass

    @abstractmethod
    def delete(self, preset_id: UUID, user_id: UUID) -> bool:
        pass
