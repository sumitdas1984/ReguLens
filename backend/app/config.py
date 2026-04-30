"""
Configuration management using Pydantic Settings.
Loads from environment variables and .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    APP_NAME: str = "ReguLens"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/regulens"

    # Alert Configuration (MVP - single recipient)
    ALERT_RECIPIENT_EMAIL: Optional[str] = None
    ALERT_RECIPIENT_NAME: str = "Tax Professional (MVP)"

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None

    # Scraping Configuration
    SCRAPE_SCHEDULE_HOUR: int = 8  # 8 AM daily
    SCRAPE_TIMEOUT_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Singleton instance
settings = Settings()
