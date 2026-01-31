import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from the backend .env file
backend_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(backend_env_path, override=False)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bank Statement Analyzer API"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/bank_statements")

    # CORS settings
    BACKEND_CORS_ORIGINS: list = [
        os.getenv("WEB_BASE_URL", "http://localhost:5173"),
    ]

    # Port configurations
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    WEB_PORT: int = int(os.getenv("WEB_PORT", "5173"))
    DB_PORT: int = int(os.getenv("DB_PORT", "54321"))

    # URL configurations
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    WEB_BASE_URL: str = os.getenv("WEB_BASE_URL", "http://localhost:5173")

    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Auth settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cookie settings (derived from API_BASE_URL)
    @property
    def COOKIE_SECURE(self) -> bool:
        return self.API_BASE_URL.startswith("https")

    @property
    def COOKIE_SAMESITE(self) -> str:
        return "none" if self.COOKIE_SECURE else "lax"

    # OAuth settings
    GOOGLE_OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    GOOGLE_OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")

    # E2E Testing
    E2E_TEST_MODE: bool = os.getenv("E2E_TEST_MODE", "").lower() == "true"

    # Stripe settings
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_ID_BASIC: str = os.getenv("STRIPE_PRICE_ID_BASIC", "")
    STRIPE_PRICE_ID_PRO: str = os.getenv("STRIPE_PRICE_ID_PRO", "")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
