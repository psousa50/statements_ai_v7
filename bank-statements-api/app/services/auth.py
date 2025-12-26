from typing import Optional, Tuple
from uuid import UUID

from app.core.auth.jwt import create_access_token, create_refresh_token, hash_refresh_token
from app.core.auth.password import hash_password, verify_password
from app.domain.models.refresh_token import RefreshToken
from app.domain.models.user import User
from app.ports.repositories.refresh_token import RefreshTokenRepository
from app.ports.repositories.user import UserRepository


class AuthTokens:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token


class AuthService:
    def __init__(self, user_repository: UserRepository, refresh_token_repository: RefreshTokenRepository):
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    def register_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
    ) -> Tuple[User, bool]:
        existing_user = self.user_repository.get_by_email(email)

        if existing_user:
            if existing_user.password_hash:
                raise ValueError("Email already registered")
            existing_user.password_hash = hash_password(password)
            if name:
                existing_user.name = name
            return self.user_repository.update(existing_user), True

        user = User(
            email=email,
            name=name,
            password_hash=hash_password(password),
        )
        return self.user_repository.create(user), False

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.user_repository.get_by_email(email)
        if not user or not user.password_hash:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def get_or_create_user_from_oauth(
        self,
        oauth_provider: str,
        oauth_id: str,
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        user = self.user_repository.get_by_oauth(oauth_provider, oauth_id)
        if user:
            if user.email != email or user.name != name or user.avatar_url != avatar_url:
                user.email = email
                user.name = name
                user.avatar_url = avatar_url
                user = self.user_repository.update(user)
            return user

        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            existing_user.oauth_provider = oauth_provider
            existing_user.oauth_id = oauth_id
            if name and not existing_user.name:
                existing_user.name = name
            if avatar_url:
                existing_user.avatar_url = avatar_url
            return self.user_repository.update(existing_user)

        user = User(
            email=email,
            name=name,
            avatar_url=avatar_url,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
        )
        return self.user_repository.create(user)

    def create_tokens_for_user(self, user: User) -> AuthTokens:
        access_token = create_access_token(user.id)
        refresh_token_value, token_hash, expires_at = create_refresh_token()

        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.refresh_token_repository.create(refresh_token)

        return AuthTokens(access_token=access_token, refresh_token=refresh_token_value)

    def refresh_access_token(self, refresh_token_value: str) -> Optional[AuthTokens]:
        token_hash = hash_refresh_token(refresh_token_value)
        refresh_token = self.refresh_token_repository.get_by_token_hash(token_hash)

        if not refresh_token or not refresh_token.is_valid:
            return None

        self.refresh_token_repository.revoke(refresh_token)

        user = self.user_repository.get_by_id(refresh_token.user_id)
        if not user:
            return None

        return self.create_tokens_for_user(user)

    def revoke_refresh_token(self, refresh_token_value: str) -> bool:
        token_hash = hash_refresh_token(refresh_token_value)
        refresh_token = self.refresh_token_repository.get_by_token_hash(token_hash)

        if not refresh_token:
            return False

        self.refresh_token_repository.revoke(refresh_token)
        return True

    def revoke_all_user_tokens(self, user_id: UUID) -> None:
        self.refresh_token_repository.revoke_all_for_user(user_id)

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        return self.user_repository.get_by_id(user_id)
