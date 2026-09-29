"""
Centralised settings, loaded from environment variables / .env
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://ml_lab_user:ml_lab_pass@localhost:5432/ml_virtual_lab"

    # --- Auth ---
    JWT_SECRET_KEY: str = "change-me-in-.env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8h, so students aren't logged out mid-lab
    BCRYPT_ROUNDS: int = 10  # ~70ms per hash; keeps a 60-student upload to a few seconds

    # --- Email (credentials emails) ---
    # EMAIL_ENABLED=false -> nothing is sent; the default password is written to the server log instead (dev only).
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""  # e.g. "ML Virtual Lab <noreply@yourcollege.edu>"
    SMTP_USE_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:5173"  # login link put in the email

    # --- Uploads ---
    MAX_UPLOAD_ROWS: int = 500

    # --- App ---
    ENV: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()
