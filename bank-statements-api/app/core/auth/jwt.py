import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import jwt

from app.core.config import settings


class TokenPayload:
    def __init__(self, user_id: UUID, exp: datetime):
        self.user_id = user_id
        self.exp = exp


def create_access_token(user_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return token, token_hash, expires_at


def decode_access_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = UUID(payload.get("sub"))
        exp = datetime.fromtimestamp(payload.get("exp"))
        if payload.get("type") != "access":
            return None
        return TokenPayload(user_id=user_id, exp=exp)
    except (jwt.PyJWTError, ValueError, KeyError):
        return None


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
