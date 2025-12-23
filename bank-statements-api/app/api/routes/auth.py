import secrets
import time
from typing import Optional

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict

from app.adapters.repositories.refresh_token import SQLAlchemyRefreshTokenRepository
from app.adapters.repositories.user import SQLAlchemyUserRepository
from app.core.auth.jwt import decode_access_token
from app.core.config import settings
from app.core.database import SessionLocal
from app.domain.models.user import User
from app.services.auth import AuthService


# In-memory store for auth codes (short-lived, one-time use)
# In production, use Redis or similar for multi-instance deployments
_auth_codes: dict[
    str, tuple[str, str, float]
] = {}  # code -> (access_token, refresh_token, expires_at)
AUTH_CODE_EXPIRY_SECONDS = 60  # 1 minute


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]


oauth = OAuth()


def _register_oauth_clients():
    if settings.GOOGLE_OAUTH_CLIENT_ID:
        oauth.register(
            name="google",
            client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile", "prompt": "select_account"},
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
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_auth_cookies(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


def _create_auth_code(access_token: str, refresh_token: str) -> str:
    """Create a short-lived, one-time auth code for token exchange.

    This is used to work around Safari ITP and other strict third-party cookie
    policies. Instead of setting cookies directly in the OAuth callback (which
    may be blocked), we redirect to the frontend with a code that can be
    exchanged for cookies via a same-origin request.
    """
    # Clean up expired codes
    current_time = time.time()
    expired_codes = [
        code
        for code, (_, _, expires_at) in _auth_codes.items()
        if expires_at < current_time
    ]
    for code in expired_codes:
        del _auth_codes[code]

    # Generate new code
    code = secrets.token_urlsafe(32)
    expires_at = current_time + AUTH_CODE_EXPIRY_SECONDS
    _auth_codes[code] = (access_token, refresh_token, expires_at)
    return code


def _exchange_auth_code(code: str) -> tuple[str, str] | None:
    """Exchange an auth code for tokens. Code is single-use."""
    if code not in _auth_codes:
        return None

    access_token, refresh_token, expires_at = _auth_codes.pop(code)
    if time.time() > expires_at:
        return None

    return access_token, refresh_token


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


def register_auth_routes(app: FastAPI):
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.get("/google")
    async def google_login(request: Request):
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google OAuth not configured",
            )
        redirect_uri = (
            f"{settings.API_BASE_URL}{settings.API_V1_STR}/auth/google/callback"
        )
        return await oauth.google.authorize_redirect(request, redirect_uri)

    @router.get("/google/callback")
    async def google_callback(request: Request):
        try:
            token = await oauth.google.authorize_access_token(request)
        except OAuthError as e:
            redirect_url = f"{settings.WEB_BASE_URL}/auth/callback?error={str(e)}"
            return RedirectResponse(url=redirect_url, status_code=302)

        user_info = token.get("userinfo")
        if not user_info:
            redirect_url = (
                f"{settings.WEB_BASE_URL}/auth/callback?error=Failed to get user info"
            )
            return RedirectResponse(url=redirect_url, status_code=302)

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

            # Create a short-lived auth code instead of setting cookies directly
            # This works around Safari ITP which blocks cross-origin cookies
            auth_code = _create_auth_code(tokens.access_token, tokens.refresh_token)
            redirect_url = f"{settings.WEB_BASE_URL}/auth/callback?code={auth_code}"
            return RedirectResponse(url=redirect_url, status_code=302)
        finally:
            db.close()

    @router.post("/refresh")
    async def refresh_token(
        response: Response, refresh_token: Optional[str] = Cookie(None)
    ):
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token"
            )

        db = SessionLocal()
        try:
            user_repo = SQLAlchemyUserRepository(db)
            refresh_token_repo = SQLAlchemyRefreshTokenRepository(db)
            auth_service = AuthService(user_repo, refresh_token_repo)

            tokens = auth_service.refresh_access_token(refresh_token)
            if not tokens:
                _clear_auth_cookies(response)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

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

    @router.post("/exchange")
    async def exchange_auth_code(response: Response, code: str):
        """Exchange a one-time auth code for session cookies.

        This endpoint is called by the frontend after OAuth callback to set
        cookies in a same-origin context, working around Safari ITP restrictions.
        """
        tokens = _exchange_auth_code(code)
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired auth code",
            )

        access_token, refresh_token = tokens
        _set_auth_cookies(response, access_token, refresh_token)
        return {"message": "Authentication successful"}

    @router.post("/test-login")
    async def test_login(response: Response):
        if not settings.E2E_TEST_MODE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Test login is only available in E2E test mode",
            )

        from app.adapters.repositories.account import SQLAlchemyAccountRepository
        from app.domain.models.account import Account

        db = SessionLocal()
        try:
            user_repo = SQLAlchemyUserRepository(db)
            refresh_token_repo = SQLAlchemyRefreshTokenRepository(db)
            auth_service = AuthService(user_repo, refresh_token_repo)

            user = auth_service.get_or_create_user_from_oauth(
                oauth_provider="test",
                oauth_id="e2e-test-user",
                email="e2e-test@example.com",
                name="E2E Test User",
                avatar_url=None,
            )

            account_repo = SQLAlchemyAccountRepository(db)
            accounts = account_repo.get_all(user.id)
            if not accounts:
                test_account = Account(
                    name="E2E Test Account",
                    user_id=user.id,
                )
                account_repo.create(test_account)
                db.commit()
                account_id = str(test_account.id)
            else:
                account_id = str(accounts[0].id)

            tokens = auth_service.create_tokens_for_user(user)
            _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
            return {
                "message": "Test login successful",
                "user_id": str(user.id),
                "account_id": account_id,
            }
        finally:
            db.close()

    app.include_router(router, prefix=settings.API_V1_STR)
