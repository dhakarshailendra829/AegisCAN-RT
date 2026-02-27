# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore',  # Ignore unknown .env keys - safe for development
    )

    # Core settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database (use async dialect for future async SQLAlchemy)
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/aegiscan.db"

    # Security (uncomment when adding JWT auth)
    SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    #  External APIs (add real keys in .env when using)
    OPENWEATHER_API_KEY: str | None = None
    NASA_POWER_API_BASE: str = "https://power.larc.nasa.gov/api"

settings = Settings()