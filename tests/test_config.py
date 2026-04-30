"""
Comprehensive tests for environment configuration.
Tests validation, defaults, type conversion, and error handling.
"""

import pytest
import os
from pydantic import ValidationError
from backend.app.config import Settings


class TestConfigurationLoading:
    """Test basic configuration loading from environment."""

    def test_config_loads_with_defaults(self, monkeypatch):
        """Test that config loads successfully with only required fields."""
        # Prevent loading from .env file by using empty string
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        monkeypatch.delenv("ALERT_RECIPIENT_EMAIL", raising=False)

        # Create settings with explicit model config to skip .env file
        from pydantic_settings import SettingsConfigDict

        class TestSettings(Settings):
            model_config = SettingsConfigDict(
                env_file=None,  # Don't load from .env
                case_sensitive=True,
            )

        settings = TestSettings()

        assert settings.APP_NAME == "ReguLens"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.DEBUG is False
        assert settings.SCRAPE_SCHEDULE_HOUR == 8
        assert settings.SCRAPE_TIMEOUT_SECONDS == 30

    def test_config_loads_from_environment(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("APP_NAME", "TestApp")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/testdb")
        monkeypatch.setenv("SCRAPE_SCHEDULE_HOUR", "14")

        settings = Settings()

        assert settings.APP_NAME == "TestApp"
        assert settings.DEBUG is True
        assert settings.SCRAPE_SCHEDULE_HOUR == 14


class TestDatabaseURLValidation:
    """Test DATABASE_URL validation."""

    def test_valid_postgresql_url(self, monkeypatch):
        """Test that valid PostgreSQL URLs are accepted."""
        valid_urls = [
            "postgresql://user:pass@localhost:5432/dbname",
            "postgresql://user@localhost/dbname",
            "postgresql://localhost/dbname",
            "postgresql+psycopg2://user:pass@host:5432/db",
        ]

        for url in valid_urls:
            monkeypatch.setenv("DATABASE_URL", url)
            settings = Settings()
            assert settings.DATABASE_URL == url

    def test_invalid_database_url_format(self, monkeypatch):
        """Test that invalid DATABASE_URL formats raise validation errors."""
        invalid_urls = [
            "mysql://user:pass@localhost/db",  # Wrong DB type
            "not-a-url",
            "postgresql://",  # Incomplete
        ]

        for url in invalid_urls:
            monkeypatch.setenv("DATABASE_URL", url)
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert "DATABASE_URL" in str(exc_info.value)

    def test_empty_database_url(self, monkeypatch):
        """Test that empty DATABASE_URL raises error."""
        monkeypatch.setenv("DATABASE_URL", "")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "cannot be empty" in str(exc_info.value)


class TestEmailValidation:
    """Test email address validation."""

    def test_valid_email_formats(self, monkeypatch):
        """Test that valid email formats are accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

        valid_emails = [
            "user@example.com",
            "test.user@company.co.uk",
            "admin+alerts@regulens.com",
            "123@domain.com",
        ]

        for email in valid_emails:
            monkeypatch.setenv("ALERT_RECIPIENT_EMAIL", email)
            settings = Settings()
            assert settings.ALERT_RECIPIENT_EMAIL == email

    def test_invalid_email_formats(self, monkeypatch):
        """Test that invalid email formats raise validation errors."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user @example.com",  # Space
            "user@domain",  # No TLD
        ]

        for email in invalid_emails:
            monkeypatch.setenv("ALERT_RECIPIENT_EMAIL", email)
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert "valid email address" in str(exc_info.value).lower()

    def test_email_is_optional(self, monkeypatch):
        """Test that email can be None/omitted."""
        from pydantic_settings import SettingsConfigDict

        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.delenv("ALERT_RECIPIENT_EMAIL", raising=False)

        class TestSettings(Settings):
            model_config = SettingsConfigDict(
                env_file=None,  # Don't load from .env
                case_sensitive=True,
            )

        settings = TestSettings()
        assert settings.ALERT_RECIPIENT_EMAIL is None


class TestAPIKeyValidation:
    """Test API key format validation."""

    def test_valid_anthropic_key(self, monkeypatch):
        """Test that valid Anthropic API key is accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv(
            "ANTHROPIC_API_KEY",
            "sk-ant-api03-" + "a" * 80  # Realistic length
        )

        settings = Settings()
        assert settings.ANTHROPIC_API_KEY.startswith("sk-ant-")

    def test_anthropic_key_strips_quotes(self, monkeypatch):
        """Test that quotes are stripped from API key."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv(
            "ANTHROPIC_API_KEY",
            '"sk-ant-api03-' + "a" * 80 + '"'
        )

        settings = Settings()
        assert not settings.ANTHROPIC_API_KEY.startswith('"')
        assert settings.ANTHROPIC_API_KEY.startswith("sk-ant-")

    def test_invalid_anthropic_key_prefix(self, monkeypatch):
        """Test that wrong prefix raises error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-invalid-key")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "sk-ant-" in str(exc_info.value)

    def test_anthropic_key_too_short(self, monkeypatch):
        """Test that too-short key raises error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-short")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "too short" in str(exc_info.value).lower()

    def test_valid_resend_key(self, monkeypatch):
        """Test that valid Resend API key is accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("RESEND_API_KEY", "re_" + "a" * 30)

        settings = Settings()
        assert settings.RESEND_API_KEY.startswith("re_")

    def test_invalid_resend_key_prefix(self, monkeypatch):
        """Test that wrong Resend prefix raises error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("RESEND_API_KEY", "invalid_key")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "re_" in str(exc_info.value)

    def test_api_keys_are_optional(self, monkeypatch):
        """Test that API keys can be None/omitted."""
        from pydantic_settings import SettingsConfigDict

        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("RESEND_API_KEY", raising=False)

        class TestSettings(Settings):
            model_config = SettingsConfigDict(
                env_file=None,  # Don't load from .env
                case_sensitive=True,
            )

        settings = TestSettings()
        assert settings.ANTHROPIC_API_KEY is None
        assert settings.RESEND_API_KEY is None


class TestNumericRangeValidation:
    """Test numeric field validation."""

    def test_valid_schedule_hours(self, monkeypatch):
        """Test that valid schedule hours (0-23) are accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

        for hour in [0, 8, 12, 23]:
            monkeypatch.setenv("SCRAPE_SCHEDULE_HOUR", str(hour))
            settings = Settings()
            assert settings.SCRAPE_SCHEDULE_HOUR == hour

    def test_invalid_schedule_hour_out_of_range(self, monkeypatch):
        """Test that out-of-range hours raise errors."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

        for hour in [-1, 24, 25, 100]:
            monkeypatch.setenv("SCRAPE_SCHEDULE_HOUR", str(hour))
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert "between 0 and 23" in str(exc_info.value)

    def test_invalid_schedule_hour_not_integer(self, monkeypatch):
        """Test that non-integer schedule hour raises error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("SCRAPE_SCHEDULE_HOUR", "not-a-number")

        with pytest.raises(ValidationError):
            Settings()

    def test_valid_timeout_values(self, monkeypatch):
        """Test that valid timeout values are accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

        for timeout in [1, 30, 60, 300]:
            monkeypatch.setenv("SCRAPE_TIMEOUT_SECONDS", str(timeout))
            settings = Settings()
            assert settings.SCRAPE_TIMEOUT_SECONDS == timeout

    def test_timeout_must_be_positive(self, monkeypatch):
        """Test that non-positive timeout raises error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

        for timeout in [0, -1, -10]:
            monkeypatch.setenv("SCRAPE_TIMEOUT_SECONDS", str(timeout))
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert "positive" in str(exc_info.value).lower()

    def test_timeout_max_limit(self, monkeypatch):
        """Test that timeout above 300s raises error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("SCRAPE_TIMEOUT_SECONDS", "301")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "should not exceed 300" in str(exc_info.value)


class TestTypeConversion:
    """Test automatic type conversion from environment variables."""

    def test_boolean_conversion(self, monkeypatch):
        """Test that string booleans are converted correctly."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

        # Test true values
        for true_value in ["true", "True", "TRUE", "1"]:
            monkeypatch.setenv("DEBUG", true_value)
            settings = Settings()
            assert settings.DEBUG is True

        # Test false values
        for false_value in ["false", "False", "FALSE", "0"]:
            monkeypatch.setenv("DEBUG", false_value)
            settings = Settings()
            assert settings.DEBUG is False

    def test_integer_conversion(self, monkeypatch):
        """Test that string integers are converted correctly."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("SCRAPE_SCHEDULE_HOUR", "14")
        monkeypatch.setenv("SCRAPE_TIMEOUT_SECONDS", "60")

        settings = Settings()

        assert isinstance(settings.SCRAPE_SCHEDULE_HOUR, int)
        assert settings.SCRAPE_SCHEDULE_HOUR == 14
        assert isinstance(settings.SCRAPE_TIMEOUT_SECONDS, int)
        assert settings.SCRAPE_TIMEOUT_SECONDS == 60


class TestSettingsSingleton:
    """Test that settings singleton works correctly."""

    def test_singleton_pattern_consistency(self):
        """Test that the singleton instance is consistent."""
        from backend.app.config import settings

        # Settings should be accessible and have expected attributes
        assert hasattr(settings, "APP_NAME")
        assert hasattr(settings, "DATABASE_URL")
        assert settings.APP_NAME == "ReguLens"

    def test_settings_can_be_imported_multiple_times(self):
        """Test that settings can be imported from multiple places."""
        from backend.app.config import settings as settings1
        from backend.app.config import settings as settings2

        # Should be the same instance
        assert settings1 is settings2


class TestErrorMessages:
    """Test that validation errors provide helpful messages."""

    def test_database_url_error_message(self, monkeypatch):
        """Test DATABASE_URL error message is helpful."""
        monkeypatch.setenv("DATABASE_URL", "invalid-url")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_msg = str(exc_info.value).lower()
        assert "postgresql" in error_msg
        assert ("format" in error_msg or "connection string" in error_msg)

    def test_email_error_message(self, monkeypatch):
        """Test email error message is helpful."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("ALERT_RECIPIENT_EMAIL", "invalid")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_msg = str(exc_info.value).lower()
        assert "email" in error_msg
        assert "valid" in error_msg

    def test_api_key_error_message(self, monkeypatch):
        """Test API key error messages are helpful."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "wrong-prefix-key")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_msg = str(exc_info.value)
        assert "sk-ant-" in error_msg
        assert ("anthropic" in error_msg.lower() or "key" in error_msg.lower())
