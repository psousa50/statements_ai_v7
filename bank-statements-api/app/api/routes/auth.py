from typing import Optional

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Cookie, Depends, FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.adapters.repositories.refresh_token import SQLAlchemyRefreshTokenRepository
from app.adapters.repositories.user import SQLAlchemyUserRepository
from app.core.auth.jwt import decode_access_token
from app.core.config import settings
from app.core.database import SessionLocal
from app.domain.models.user import User
from app.services.auth import AuthService


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]

    class Config:
        from_attributes = True


oauth = OAuth()


def _register_oauth_clients():
    if settings.GOOGLE_OAUTH_CLIENT_ID:
        oauth.register(
            name="google",
            client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )


_register_oauth_clients()


def _get_auth_service() -> AuthService:
    db = SessionLocal()
    try:
        user_repo = SQLAlchemyUserRepository(db)
        refresh_token_repo = SQLAlchemyRefreshTokenRepository(db)
        return AuthService(user_repo, refresh_token_repo)
    finally:
        pass


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.API_BASE_URL.startswith("https"),
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.API_BASE_URL.startswith("https"),
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_auth_cookies(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(None),
) -> Optional[User]:
    if not access_token:
        return None

    payload = decode_access_token(access_token)
    if not payload:
        return None

    db = SessionLocal()
    try:
        user_repo = SQLAlchemyUserRepository(db)
        return user_repo.get_by_id(payload.user_id)
    finally:
        db.close()


def require_current_user(
    access_token: Optional[str] = Cookie(None),
) -> User:
    user = get_current_user_from_cookie(access_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def register_auth_routes(app: FastAPI):
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.get("/google")
    async def google_login(request: Request):
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured")
        redirect_uri = f"{settings.API_BASE_URL}{settings.API_V1_STR}/auth/google/callback"
        return await oauth.google.authorize_redirect(request, redirect_uri)

    @router.get("/google/callback")
    async def google_callback(request: Request, response: Response):
        try:
            token = await oauth.google.authorize_access_token(request)
        except OAuthError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        user_info = token.get("userinfo")
        if not user_info:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info")

        db = SessionLocal()
        try:
            user_repo = SQLAlchemyUserRepository(db)
            refresh_token_repo = SQLAlchemyRefreshTokenRepository(db)
            auth_service = AuthService(user_repo, refresh_token_repo)

            user = auth_service.get_or_create_user_from_oauth(
                oauth_provider="google",
                oauth_id=user_info["sub"],
                email=user_info["email"],
                name=user_info.get("name"),
                avatar_url=user_info.get("picture"),
            )

            tokens = auth_service.create_tokens_for_user(user)
            _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
            response.status_code = status.HTTP_302_FOUND
            response.headers["Location"] = settings.WEB_BASE_URL
            return response
        finally:
            db.close()

    @router.post("/refresh")
    async def refresh_token(response: Response, refresh_token: Optional[str] = Cookie(None)):
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

        db = SessionLocal()
        try:
            user_repo = SQLAlchemyUserRepository(db)
            refresh_token_repo = SQLAlchemyRefreshTokenRepository(db)
            auth_service = AuthService(user_repo, refresh_token_repo)

            tokens = auth_service.refresh_access_token(refresh_token)
            if not tokens:
                _clear_auth_cookies(response)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

            _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
            return {"message": "Token refreshed"}
        finally:
            db.close()

    @router.post("/logout")
    async def logout(response: Response, refresh_token: Optional[str] = Cookie(None)):
        if refresh_token:
            db = SessionLocal()
            try:
                user_repo = SQLAlchemyUserRepository(db)
                refresh_token_repo = SQLAlchemyRefreshTokenRepository(db)
                auth_service = AuthService(user_repo, refresh_token_repo)
                auth_service.revoke_refresh_token(refresh_token)
            finally:
                db.close()

        _clear_auth_cookies(response)
        return {"message": "Logged out"}

    @router.get("/me", response_model=UserResponse)
    async def get_current_user(user: User = Depends(require_current_user)):
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
        )

    app.include_router(router, prefix=settings.API_V1_STR)
