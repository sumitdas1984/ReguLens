# Spec for Configure Environment Variables and .env File

branch: claude/feature/env-configuration

## Summary
Set up environment configuration with .env file for local development. This ensures all configuration is managed through environment variables, API keys are never hardcoded, and the application can be easily configured for different environments (local development, testing, production).

**Note**: `.env.example` and `config.py` already exist from the initial project setup. This spec validates completeness and identifies any gaps.

## Functional Requirements
- `.env.example` template exists with all required variables documented
- Local `.env` file can be created from `.env.example` for development
- `config.py` uses Pydantic Settings to load environment variables
- All sensitive data (API keys, database credentials) loaded from environment
- Database connection string configured for local PostgreSQL
- Alert recipient email configuration included
- API key placeholders for external services (Anthropic, Resend)
- Environment variables for scraping configuration (schedule, timeout)
- Debug mode flag for development
- Application metadata (name, version)

## Possible Edge Cases
- `.env` file must be in `.gitignore` to prevent committing secrets
- Missing required environment variables should fail gracefully with clear error messages
- Environment variable type validation (e.g., integers for ports, booleans for flags)
- Optional vs required environment variables clearly distinguished
- Default values provided for non-sensitive configuration
- Connection string format validation for DATABASE_URL
- Email address format validation for ALERT_RECIPIENT_EMAIL

## Acceptance Criteria
- `.env.example` exists at project root with all required variables
- `.env.example` includes comments explaining each variable
- `.env` is listed in `.gitignore` (must not be committed)
- `config.py` uses `pydantic-settings` BaseSettings class
- `config.py` loads from `.env` file automatically
- `config.py` validates required fields and provides helpful error messages
- Database URL configured for local PostgreSQL: `postgresql://regulens_user:regulens_pass@localhost:5432/regulens`
- API key placeholders present: `ANTHROPIC_API_KEY`, `RESEND_API_KEY`
- Alert configuration variables present: `ALERT_RECIPIENT_EMAIL`, `ALERT_RECIPIENT_NAME`
- Scraping configuration variables present: `SCRAPE_SCHEDULE_HOUR`, `SCRAPE_TIMEOUT_SECONDS`
- Application can start without errors when `.env` is properly configured
- Settings can be imported and accessed: `from backend.app.config import settings`
- Type hints present for all configuration fields

## Open Questions
- Do we need different configuration profiles (dev, staging, prod)?
- Should we add validation for API key format (e.g., Anthropic keys start with "sk-ant-")?
- Do we need configuration for logging levels?
- Should we add configuration for CORS origins when exposing API?

## Testing Guidelines
Create test file(s) in the ./tests folder for configuration:
- Test that config loads successfully from environment variables
- Test that missing required variables raise appropriate errors
- Test that default values are applied correctly
- Test that type conversion works (strings to integers, booleans)
- Test that Settings singleton pattern works correctly
- Verify DATABASE_URL format is valid PostgreSQL connection string
