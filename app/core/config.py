import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

# Determine the base directory of the project
# This assumes config.py is in app/core/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Load the .env file from the base directory
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Formflow"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Comma-separated list of frontend origins allowed to call the API
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        case_sensitive = True

settings = Settings()

print(f"Loaded DATABASE_URL: {settings.DATABASE_URL}")
print(f"Loaded SECRET_KEY: {'*' * 8 if settings.SECRET_KEY else 'Not Set'}")