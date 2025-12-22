from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

oauth = OAuth()


def get_google_oauth_client():
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    return oauth.google
