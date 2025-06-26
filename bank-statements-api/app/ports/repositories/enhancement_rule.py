from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.enhancement_rule import EnhancementRule


class EnhancementRuleRepository(ABC):
    """Repository interface for enhancement rules"""

    @abstractmethod
    def get_all(self) -> List[EnhancementRule]:
        """Get all enhancement rules"""
        pass

    @abstractmethod
    def save(self, rule: EnhancementRule) -> EnhancementRule:
        """Save an enhancement rule"""
        pass

    @abstractmethod
    def find_by_id(self, rule_id: UUID) -> Optional[EnhancementRule]:
        """Find enhancement rule by ID"""
        pass

    @abstractmethod
    def find_by_normalized_description(self, normalized_description: str) -> List[EnhancementRule]:
        """Find enhancement rules matching a normalized description pattern"""
        pass

    @abstractmethod
    def delete(self, rule_id: UUID) -> bool:
        """Delete an enhancement rule by ID"""
        pass
