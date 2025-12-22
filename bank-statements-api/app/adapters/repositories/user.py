from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.user import User
from app.ports.repositories.user import UserRepository


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, user: User) -> User:
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db_session.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db_session.query(User).filter(User.email == email).first()

    def get_by_oauth(self, oauth_provider: str, oauth_id: str) -> Optional[User]:
        return self.db_session.query(User).filter(User.oauth_provider == oauth_provider, User.oauth_id == oauth_id).first()

    def update(self, user: User) -> User:
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def delete(self, user_id: UUID) -> None:
        user = self.get_by_id(user_id)
        if user:
            self.db_session.delete(user)
            self.db_session.commit()
