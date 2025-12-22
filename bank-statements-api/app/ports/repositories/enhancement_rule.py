from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.enhancement_rule import EnhancementRule


class EnhancementRuleRepository(ABC):
    @abstractmethod
    def get_all(self, user_id: UUID) -> List[EnhancementRule]:
        pass

    @abstractmethod
    def save(self, rule: EnhancementRule) -> EnhancementRule:
        pass

    @abstractmethod
    def find_by_id(self, rule_id: UUID, user_id: UUID) -> Optional[EnhancementRule]:
        pass

    @abstractmethod
    def find_by_normalized_description(self, normalized_description: str, user_id: UUID) -> List[EnhancementRule]:
        pass

    @abstractmethod
    def delete(self, rule: EnhancementRule) -> None:
        pass

    @abstractmethod
    def find_matching_rules_batch(self, normalized_descriptions: List[str], user_id: UUID) -> List[EnhancementRule]:
        pass
