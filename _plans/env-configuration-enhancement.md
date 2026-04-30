# Implementation Plan: Environment Configuration Enhancement

## Context

This plan enhances the existing environment configuration for ReguLens MVP by adding field validation, comprehensive testing, and better error messages.

**Why this change is needed:**
- Current `.env.example` and `config.py` exist and work but lack validation
- Invalid configurations (wrong email format, bad database URLs, invalid API keys) are not caught early
- No comprehensive test coverage for configuration (only 1 basic test exists)
- Production systems need robust validation with helpful error messages

**Current State:**
- ✅ `.env.example` exists with all required variables (8 categories)
- ✅ `config.py` uses Pydantic Settings correctly with singleton pattern
- ✅ `.env` is in `.gitignore`
- ✅ Basic integration with `database.py` and `dependencies.py` works
- ❌ No field validators for email, URL, or API key formats
- ❌ Only 1 test in `test_structure.py::test_config_loads_from_env()`
- ❌ No helpful error messages for invalid configurations

**Goal:** Add field validation, create comprehensive test suite, and ensure production-ready configuration management.

---

## Implementation Steps

### Step 1: Enhance config.py with Field Validators

**File:** `backend/app/config.py`

#### 1.1 Add imports
Add after line 7 (after existing imports):
```python
from pydantic import field_validator
import re
```

#### 1.2 Add field docstrings to Settings class
Update each field (lines 10-37) to include docstrings explaining purpose and validation rules.

Example:
```python
DATABASE_URL: str = "postgresql://user:password@localhost:5432/regulens"
"""PostgreSQL connection string. Format: postgresql://user:pass@host:port/dbname"""
```

#### 1.3 Add six field validators

Add these validators before the closing of Settings class (after `model_config`):

**1. DATABASE_URL validator:**
- Check not empty
- Validate PostgreSQL URL format using regex: `^postgresql(\+\w+)?://([^:@]+(?::[^@]+)?@)?([^:/]+)(:\d+)?(/[^?]+)?(\?.+)?$`
- Helpful error message with expected format

**2. ALERT_RECIPIENT_EMAIL validator:**
- Allow None (optional field)
- Validate email format with regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Clear error message showing the invalid value

**3. ANTHROPIC_API_KEY validator:**
- Allow None (optional field)
- Strip quotes (common .env formatting issue)
- Check prefix is "sk-ant-"
- Check length is at least 50 characters
- Error message mentioning Anthropic Console

**4. RESEND_API_KEY validator:**
- Allow None (optional field)
- Strip quotes
- Check prefix is "re_"
- Error message mentioning Resend dashboard

**5. SCRAPE_SCHEDULE_HOUR validator:**
- Check is integer type
- Validate range 0-23 (hours in a day)
- Clear error message with valid range

**6. SCRAPE_TIMEOUT_SECONDS validator:**
- Check is integer type
- Must be positive (> 0)
- Maximum 300 seconds (5 minutes)
- Clear error message with limits

**Validator Pattern (Pydantic v2):**
```python
@field_validator("FIELD_NAME")
@classmethod
def validate_field_name(cls, v: Type) -> Type:
    """Validator docstring."""
    # Validation logic
    if invalid:
        raise ValueError("Clear error message with examples")
    return v
```

---

### Step 2: Create Comprehensive Test Suite

**File:** `tests/test_config.py` (NEW FILE)

Create ~400-500 lines of test code organized into 8 test classes:

#### Test Classes:

1. **TestConfigurationLoading** - Basic loading and defaults
   - `test_config_loads_with_defaults()` - Loads with minimal required fields
   - `test_config_loads_from_environment()` - Environment overrides defaults

2. **TestDatabaseURLValidation** - DATABASE_URL validation
   - `test_valid_postgresql_url()` - Accept valid PostgreSQL URLs
   - `test_invalid_database_url_format()` - Reject invalid formats
   - `test_empty_database_url()` - Reject empty URL

3. **TestEmailValidation** - Email format validation
   - `test_valid_email_formats()` - Accept valid emails
   - `test_invalid_email_formats()` - Reject invalid emails
   - `test_email_is_optional()` - Allow None for optional field

4. **TestAPIKeyValidation** - API key format validation
   - `test_valid_anthropic_key()` - Accept valid Anthropic keys
   - `test_anthropic_key_strips_quotes()` - Strip quotes from .env
   - `test_invalid_anthropic_key_prefix()` - Reject wrong prefix
   - `test_anthropic_key_too_short()` - Reject short keys
   - `test_valid_resend_key()` - Accept valid Resend keys
   - `test_invalid_resend_key_prefix()` - Reject wrong prefix
   - `test_api_keys_are_optional()` - Allow None for optional fields

5. **TestNumericRangeValidation** - Numeric field validation
   - `test_valid_schedule_hours()` - Accept 0-23
   - `test_invalid_schedule_hour_out_of_range()` - Reject <0 or >23
   - `test_invalid_schedule_hour_not_integer()` - Reject non-integers
   - `test_valid_timeout_values()` - Accept valid timeouts
   - `test_timeout_must_be_positive()` - Reject <=0
   - `test_timeout_max_limit()` - Reject >300

6. **TestTypeConversion** - Environment variable type conversion
   - `test_boolean_conversion()` - Convert string "true"/"false" to bool
   - `test_integer_conversion()` - Convert string numbers to int

7. **TestSettingsSingleton** - Singleton pattern verification
   - `test_singleton_pattern_consistency()` - Singleton instance works
   - `test_settings_can_be_imported_multiple_times()` - Same instance

8. **TestErrorMessages** - Error message quality
   - `test_database_url_error_message()` - Helpful DATABASE_URL errors
   - `test_email_error_message()` - Helpful email errors
   - `test_api_key_error_message()` - Helpful API key errors

**Test Utilities:**
- Use `pytest.fixture` and `monkeypatch` for environment isolation
- Use `pytest.raises(ValidationError)` to test validators
- Test both positive (valid) and negative (invalid) cases

---

### Step 3: Update .env.example (Optional Enhancement)

**File:** `.env.example`

Add brief comments explaining validation rules for key fields:

```bash
# Database (local PostgreSQL - must be valid PostgreSQL URL)
DATABASE_URL=postgresql://regulens_user:regulens_pass@localhost:5432/regulens

# Alert Configuration (email must be valid format)
ALERT_RECIPIENT_EMAIL=your-email@example.com

# API Keys (Anthropic keys start with sk-ant-, Resend keys start with re_)
ANTHROPIC_API_KEY=sk-ant-...
RESEND_API_KEY=re_...

# Scraping Configuration (hour must be 0-23, timeout must be positive)
SCRAPE_SCHEDULE_HOUR=8
SCRAPE_TIMEOUT_SECONDS=30
```

---

## Verification Steps

### 1. Run Test Suite
```bash
# Run all config tests
uv run pytest tests/test_config.py -v

# Expected: 30+ tests pass
# Expected: Test coverage ~95%+ for config.py
```

### 2. Test Valid Configuration
```bash
# Start app with valid .env
uv run uvicorn backend.app.main:app --reload

# Expected: App starts without errors
# Test endpoint: curl http://localhost:8000/
# Expected: {"status": "ok", "message": "ReguLens API is running"}
```

### 3. Test Invalid Configurations

Create temporary invalid `.env` files to verify validation:

**Test 1: Invalid DATABASE_URL**
```bash
DATABASE_URL=mysql://wrong:db@localhost/test
# Expected error: "DATABASE_URL must be a valid PostgreSQL connection string"
```

**Test 2: Invalid email**
```bash
ALERT_RECIPIENT_EMAIL=not-an-email
# Expected error: "ALERT_RECIPIENT_EMAIL must be a valid email address"
```

**Test 3: Invalid schedule hour**
```bash
SCRAPE_SCHEDULE_HOUR=25
# Expected error: "SCRAPE_SCHEDULE_HOUR must be between 0 and 23"
```

**Test 4: Invalid API key**
```bash
ANTHROPIC_API_KEY=wrong-prefix-key
# Expected error: "ANTHROPIC_API_KEY must start with 'sk-ant-'"
```

### 4. Verify No Breaking Changes
```bash
# Existing test should still pass
uv run pytest tests/test_structure.py::test_config_loads_from_env -v

# Database connection should work
uv run python -c "from backend.app.database import engine; print('✓ Database engine created')"

# Settings dependency injection should work
uv run python -c "from backend.app.dependencies import get_settings; s = get_settings(); print(f'✓ Settings: {s.APP_NAME}')"
```

---

## Acceptance Criteria Checklist

- [ ] `config.py` has field validators for all 6 validation requirements
- [ ] Field validators use Pydantic v2 `@field_validator` decorator
- [ ] All validators have clear error messages with examples
- [ ] `tests/test_config.py` created with 30+ test cases
- [ ] Tests organized into 8 logical test classes
- [ ] All tests pass with pytest
- [ ] App starts successfully with valid `.env`
- [ ] App fails gracefully with helpful messages for invalid config
- [ ] Existing integrations (`database.py`, `dependencies.py`) still work
- [ ] No breaking changes to existing valid configurations
- [ ] Optional fields (API keys, email) can be None
- [ ] Required fields (DATABASE_URL) are validated

---

## Critical Files

1. **`backend/app/config.py`** - Main implementation
   - Add imports (2 lines)
   - Add field docstrings (~20 lines)
   - Add 6 validators (~150 lines)

2. **`tests/test_config.py`** - New comprehensive test file
   - 8 test classes
   - 30+ test methods
   - ~400-500 lines total

3. **`.env.example`** - Optional comments update
   - Add validation hints to comments
   - ~10 lines modified

4. **Integration verification:**
   - `backend/app/database.py` (line 9, 13, 15) - uses `settings.DATABASE_URL`
   - `backend/app/dependencies.py` (line 7, 22) - uses `settings` singleton
   - `tests/test_structure.py` (line 86-91) - existing config test

---

## Implementation Time Estimate

- **config.py enhancements**: 30-45 minutes
- **test_config.py creation**: 60-90 minutes
- **Testing and fixes**: 20-30 minutes
- **.env.example updates**: 5 minutes
- **Total**: 2-3 hours

---

## Success Criteria

After implementation:

1. ✅ **Robust validation** catches configuration errors early
2. ✅ **Helpful error messages** guide users to fix issues
3. ✅ **Comprehensive test coverage** ensures reliability
4. ✅ **No breaking changes** to existing valid configurations
5. ✅ **Production-ready** configuration management
