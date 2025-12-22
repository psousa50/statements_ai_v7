from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.refresh_token import RefreshToken
from app.ports.repositories.refresh_token import RefreshTokenRepository


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db_session.add(refresh_token)
        self.db_session.commit()
        self.db_session.refresh(refresh_token)
        return refresh_token

    def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        return self.db_session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    def get_by_user_id(self, user_id: UUID) -> List[RefreshToken]:
        return self.db_session.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()

    def revoke(self, refresh_token: RefreshToken) -> RefreshToken:
        refresh_token.revoked_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(refresh_token)
        return refresh_token

    def revoke_all_for_user(self, user_id: UUID) -> None:
        self.db_session.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": datetime.now(timezone.utc)})
        self.db_session.commit()

    def delete_expired(self) -> int:
        count = self.db_session.query(RefreshToken).filter(RefreshToken.expires_at < datetime.now(timezone.utc)).delete()
        self.db_session.commit()
        return count
