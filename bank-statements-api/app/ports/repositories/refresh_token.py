from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    def create(self, refresh_token: RefreshToken) -> RefreshToken:
        pass

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> List[RefreshToken]:
        pass

    @abstractmethod
    def revoke(self, refresh_token: RefreshToken) -> RefreshToken:
        pass

    @abstractmethod
    def revoke_all_for_user(self, user_id: UUID) -> None:
        pass

    @abstractmethod
    def delete_expired(self) -> int:
        pass
