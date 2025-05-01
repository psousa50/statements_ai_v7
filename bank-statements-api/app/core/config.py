import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bank Statement Analyzer API"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bank_statements")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "https://bank-statements-web-test.fly.dev"]

settings = Settings()
