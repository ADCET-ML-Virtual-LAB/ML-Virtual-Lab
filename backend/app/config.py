"""
Centralised settings, loaded from environment variables / .env
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://ml_lab_user:ml_lab_pass@localhost:5432/ml_virtual_lab"

    # --- Auth ---
    JWT_SECRET_KEY: str = "change-me-in-.env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- App ---
    ENV: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
