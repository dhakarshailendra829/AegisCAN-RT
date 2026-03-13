"""
Application configuration management.

Supports:
- SQLite (development)
- PostgreSQL (production)
- MySQL (production)

Configuration is loaded from .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from urllib.parse import urlparse


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore',
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/aegiscan.db"
    
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False

    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENWEATHER_API_KEY: Optional[str] = None
    NASA_POWER_API_BASE: str = "https://power.larc.nasa.gov/api"

    MAX_TELEMETRY_BUFFER: int = 500
    TELEMETRY_RETENTION_DAYS: int = 30

    UDP_IP: str = "127.0.0.1"
    UDP_PORT: int = 5005
    CAN_CHANNEL: str = "vcan0"
    STEERING_SCALE_FACTOR: float = 900.0 / 255.0

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return "sqlite" in self.DATABASE_URL.lower()

    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.DATABASE_URL.lower()

    @property
    def is_mysql(self) -> bool:
        """Check if using MySQL database."""
        return "mysql" in self.DATABASE_URL.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"

settings = Settings()