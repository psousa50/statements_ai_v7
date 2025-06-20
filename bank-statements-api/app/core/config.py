import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from the backend .env file
backend_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(backend_env_path)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bank Statement Analyzer API"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # CORS settings
    BACKEND_CORS_ORIGINS: list = [
        "*",
        os.getenv("WEB_BASE_URL", "http://localhost:5173"),
        "https://bank-statements-web-test.fly.dev",
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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
