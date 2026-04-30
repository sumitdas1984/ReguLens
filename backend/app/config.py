"""
Configuration management using Pydantic Settings.
Loads from environment variables and .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional
import re


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Application
    APP_NAME: str = "ReguLens"
    """Application name for display and logging."""

    APP_VERSION: str = "0.1.0"
    """Semantic version of the application."""

    DEBUG: bool = False
    """Enable debug mode for development. Shows SQL queries and detailed errors."""

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/regulens"
    """PostgreSQL connection string. Format: postgresql://user:pass@host:port/dbname"""

    # Alert Configuration (MVP - single recipient)
    ALERT_RECIPIENT_EMAIL: Optional[str] = None
    """Email address to receive regulatory alerts. Must be valid email format."""

    ALERT_RECIPIENT_NAME: str = "Tax Professional (MVP)"
    """Display name for alert recipient."""

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    """Anthropic API key for Claude AI. Should start with 'sk-ant-'."""

    RESEND_API_KEY: Optional[str] = None
    """Resend API key for email delivery. Should start with 're_'."""

    # Scraping Configuration
    SCRAPE_SCHEDULE_HOUR: int = 8
    """Hour of day (0-23) to run scheduled scraping. Default: 8 AM."""

    SCRAPE_TIMEOUT_SECONDS: int = 30
    """HTTP request timeout in seconds. Must be positive integer."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL is a valid PostgreSQL connection string."""
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")

        # PostgreSQL URL pattern: postgresql://[user[:password]@][host][:port][/dbname]
        postgres_pattern = r"^postgresql(\+\w+)?://([^:@]+(?::[^@]+)?@)?([^:/]+)(:\d+)?(/[^?]+)?(\?.+)?$"

        if not re.match(postgres_pattern, v):
            raise ValueError(
                "DATABASE_URL must be a valid PostgreSQL connection string. "
                "Expected format: postgresql://user:password@host:port/dbname"
            )

        return v

    @field_validator("ALERT_RECIPIENT_EMAIL")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided."""
        if v is None:
            return v

        # Basic email pattern validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, v):
            raise ValueError(
                f"ALERT_RECIPIENT_EMAIL must be a valid email address. Got: {v}"
            )

        return v

    @field_validator("ANTHROPIC_API_KEY")
    @classmethod
    def validate_anthropic_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate Anthropic API key format if provided."""
        if v is None:
            return v

        # Strip quotes if present (from .env file)
        v = v.strip('"').strip("'")

        if not v.startswith("sk-ant-"):
            raise ValueError(
                "ANTHROPIC_API_KEY must start with 'sk-ant-'. "
                "Please check your API key from the Anthropic Console."
            )

        # Basic length check (Anthropic keys are typically 100+ chars)
        if len(v) < 50:
            raise ValueError(
                "ANTHROPIC_API_KEY appears too short. "
                "Please verify you copied the complete key."
            )

        return v

    @field_validator("RESEND_API_KEY")
    @classmethod
    def validate_resend_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate Resend API key format if provided."""
        if v is None:
            return v

        # Strip quotes if present
        v = v.strip('"').strip("'")

        if not v.startswith("re_"):
            raise ValueError(
                "RESEND_API_KEY must start with 're_'. "
                "Please check your API key from the Resend dashboard."
            )

        return v

    @field_validator("SCRAPE_SCHEDULE_HOUR")
    @classmethod
    def validate_schedule_hour(cls, v: int) -> int:
        """Validate schedule hour is in valid range (0-23)."""
        if not isinstance(v, int):
            raise ValueError(f"SCRAPE_SCHEDULE_HOUR must be an integer. Got: {type(v)}")

        if not 0 <= v <= 23:
            raise ValueError(
                f"SCRAPE_SCHEDULE_HOUR must be between 0 and 23 (hours in a day). Got: {v}"
            )

        return v

    @field_validator("SCRAPE_TIMEOUT_SECONDS")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is a positive integer."""
        if not isinstance(v, int):
            raise ValueError(f"SCRAPE_TIMEOUT_SECONDS must be an integer. Got: {type(v)}")

        if v <= 0:
            raise ValueError(
                f"SCRAPE_TIMEOUT_SECONDS must be positive. Got: {v}"
            )

        if v > 300:  # 5 minutes max
            raise ValueError(
                f"SCRAPE_TIMEOUT_SECONDS should not exceed 300 seconds (5 minutes). Got: {v}"
            )

        return v


# Singleton instance
settings = Settings()
