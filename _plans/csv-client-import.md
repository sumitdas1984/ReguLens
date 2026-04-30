# Implementation Plan: CSV Client Import Script

## Context

This plan implements a Python script to import 100 sample client profiles from a CSV file into the PostgreSQL database.

**Why this change is needed:**
- The database models (Client, Publication, Alert) are now in place from PR #36
- A CSV file with 100 sample client profiles already exists at `data/sample/client_profiles_mvp.csv`
- These 100 clients are needed to test scrapers, AI matching, and alert generation in the MVP
- Manual import via SQL is error-prone and doesn't scale
- An automated, idempotent import script enables reliable data seeding

**Current State:**
- ✅ Client model fully defined in `backend/app/models/client.py` (11 fields)
- ✅ Database schema created via Alembic migration
- ✅ PostgreSQL running via Docker Compose
- ✅ CSV file exists: `data/sample/client_profiles_mvp.csv` (100 rows + header)
- ✅ Database session patterns established in `backend/app/database.py`
- ✅ Test patterns for bulk insert in `tests/test_models.py`
- ❌ No import script exists yet
- ❌ scripts/ directory only has README.md

**CSV File Format:**
- **Location:** `data/sample/client_profiles_mvp.csv`
- **Rows:** 101 total (1 header + 100 data)
- **Boolean format:** `True`/`False` strings
- **Tax credits format:** Pipe-delimited (e.g., `R&D|Other`)
- **Columns:** id, name, entity_type, industry, industry_naics, ca_nexus, tx_nexus, fl_nexus, revenue_range, tax_credits_used, created_at, updated_at

**Goal:** Create `scripts/import_clients.py` to import 100 client profiles with full error handling, idempotency, and progress logging.

---

## Implementation Steps

### Step 1: Create Import Script Structure

**File:** `scripts/import_clients.py` (NEW, ~300-400 lines)

**Required imports:**
```python
import argparse
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import Client
```

**Module docstring with usage examples:**
```python
"""
Import client profiles from CSV file into PostgreSQL database.

Usage:
    python scripts/import_clients.py data/sample/client_profiles_mvp.csv
    python scripts/import_clients.py data/sample/client_profiles_mvp.csv --dry-run
    python scripts/import_clients.py data/sample/client_profiles_mvp.csv --force

This script is idempotent - running multiple times will not create duplicates.
"""
```

---

### Step 2: Implement CSV Parsing Functions

**parse_boolean(value: str) -> bool**
- Convert 'True' → True, 'False' → False
- Handle empty string as False (for safety)
- Raise ValueError for invalid values
- Critical for ca_nexus, tx_nexus, fl_nexus fields

**parse_tax_credits(value: str) -> List[str]**
- Split on '|' delimiter
- Strip whitespace from each item
- Return empty list for empty string
- Examples: 'R&D|Other' → ['R&D', 'Other'], '' → []

**parse_csv_row(row: Dict[str, str], row_number: int) -> Client**

Logic:
1. Validate required fields: name, entity_type, industry, revenue_range
2. Strip whitespace from all string fields
3. Convert booleans using parse_boolean()
4. Parse tax_credits_used using parse_tax_credits()
5. Handle optional industry_naics (empty → None)
6. Create Client object WITHOUT id, created_at, updated_at (DB auto-generates)
7. Raise ValueError with row number for parsing errors

**Important:** Do NOT use CSV's 'id' column - let database generate new UUIDs

**read_csv_file(csv_path: Path) -> List[Client]**

Process:
1. Check file exists (FileNotFoundError if not)
2. Open with csv.DictReader
3. Validate expected columns present
4. Parse each row with parse_csv_row()
5. Log warnings for failed rows but continue
6. Return list of successfully parsed Clients

---

### Step 3: Implement Database Operations

**check_existing_clients(db: Session, client_names: List[str]) -> Dict[str, bool]**

Efficient duplicate detection:
```python
existing = db.query(Client.name).filter(Client.name.in_(client_names)).all()
existing_names = {name for (name,) in existing}
return {name: (name in existing_names) for name in client_names}
```

Benefits: Single query, O(1) lookup

**import_clients(db: Session, clients: List[Client], skip_existing: bool, batch_size: int) -> Dict[str, Any]**

Algorithm:
1. Initialize stats: total, inserted, skipped, failed
2. Query existing clients by name
3. Filter out existing if skip_existing=True
4. Process in batches of N (default 50):
   - Use db.bulk_save_objects(batch)
   - Commit after each batch
   - On error: rollback, log, continue
5. Return statistics dictionary

**delete_all_clients(db: Session) -> int**

For --force flag only:
```python
count = db.query(Client).count()
db.query(Client).delete()
db.commit()
return count
```

---

### Step 4: Implement CLI Interface

**parse_arguments() -> argparse.Namespace**

Arguments:
- **Positional:** `csv_file` (required) - Path to CSV file
- **Flags:**
  - `--dry-run` - Validate without importing
  - `--force` - Delete existing clients and reimport
  - `--skip-existing` (default True) - Skip existing clients
  - `--batch-size` (default 50) - Records per batch

**Usage examples:**
```bash
# Normal import
python scripts/import_clients.py data/sample/client_profiles_mvp.csv

# Dry run
python scripts/import_clients.py data/sample/client_profiles_mvp.csv --dry-run

# Force reimport (delete all first)
python scripts/import_clients.py data/sample/client_profiles_mvp.csv --force
```

---

### Step 5: Implement Main Function and Output

**print_summary(stats: Dict, elapsed_time: float) -> int**

Output format:
```
============================================================
IMPORT SUMMARY
============================================================
Total clients in CSV:  100
Successfully inserted: 95
Skipped (existing):    5
Failed:                0
Elapsed time:          2.34 seconds
============================================================

Import completed successfully!
```

Return codes:
- 0 if no failures
- 1 if any failures

**main() -> int**

Workflow:
1. Parse arguments
2. Check CSV file exists
3. Read and parse CSV
4. Connect to database
5. Handle --dry-run mode (exit before import)
6. Handle --force mode (delete + confirm)
7. Import clients
8. Print summary
9. Return exit code

Error handling:
- FileNotFoundError → clear message, exit 1
- SQLAlchemyError → database connection error, exit 1
- KeyboardInterrupt → cleanup, exit 1

---

### Step 6: Create Comprehensive Tests

**File:** `tests/test_import_clients.py` (NEW, ~400-500 lines)

**Test classes:**

1. **TestParsingFunctions** (8-10 tests)
   - test_parse_boolean_valid() - True/False handling
   - test_parse_boolean_empty() - Empty string → False
   - test_parse_boolean_invalid() - Raises ValueError
   - test_parse_tax_credits_multiple() - Pipe-delimited
   - test_parse_tax_credits_empty() - Empty list
   - test_parse_csv_row_complete() - All fields
   - test_parse_csv_row_minimal() - Required only
   - test_parse_csv_row_missing_required() - ValueError

2. **TestDatabaseOperations** (6-8 tests, uses test_db fixture)
   - test_check_existing_clients()
   - test_import_clients_new()
   - test_import_clients_skip_existing()
   - test_import_clients_batch_failure()
   - test_delete_all_clients()

3. **TestIdempotency** (3-4 tests, uses test_db fixture)
   - test_import_twice_skips_all()
   - test_force_reimport()
   - test_partial_import_recovery()

4. **TestEdgeCases** (5-6 tests)
   - test_csv_file_not_found()
   - test_empty_csv()
   - test_malformed_row()
   - test_database_connection_failure()

**Test fixture reuse:**
```python
from tests.test_models import test_db  # Reuse existing fixture
```

---

## Idempotency Strategy

**Default behavior: Skip existing clients**

Implementation:
- Query database for all client names before import
- Filter out clients whose names already exist
- Only import new clients
- Log skipped clients

**Force reimport option (--force flag):**
1. Prompt user: "WARNING: --force will DELETE ALL existing clients. Continue? (yes/no): "
2. Require exact "yes" response
3. Delete all existing clients
4. Proceed with normal import

Safety: Clear warning + explicit confirmation required

---

## Error Handling

### File Errors
- CSV not found → FileNotFoundError with clear message
- Malformed CSV → csv.Error caught and reported

### Data Errors
- Invalid boolean → Log warning, skip row
- Missing required field → Log warning, skip row
- Invalid tax credits format → Parse as best effort

### Database Errors
- Connection failure → SQLAlchemyError caught, exit 1
- Integrity constraint → Rollback batch, log, continue
- Batch failure → Rollback, increment failed count

### Script Interruption
- KeyboardInterrupt → Print message, cleanup, exit 1
- Always close database session in finally block

---

## Progress and Logging

**During parsing:**
```
Reading CSV file: data/sample/client_profiles_mvp.csv
Successfully parsed 100 clients
```

**During import:**
```
Connecting to database...
Database connection successful

Importing 100 clients in batches of 50...
  Batch 1/2: Inserted 50 clients
  Batch 2/2: Inserted 50 clients
```

**Warnings:**
```
WARNING: Row 45: Invalid boolean value 'YES'. Skipping row.
```

**Errors:**
```
ERROR: Batch 2 failed (IntegrityError): duplicate key constraint
```

---

## Verification Steps

### 1. Test Parsing Logic
```bash
# Dry run to validate CSV parsing
python scripts/import_clients.py data/sample/client_profiles_mvp.csv --dry-run

# Expected: "Would import 100 clients" with no errors
```

### 2. Test First Import
```bash
# Import for the first time
python scripts/import_clients.py data/sample/client_profiles_mvp.csv

# Expected: "Successfully inserted: 100"
```

### 3. Verify Database
```bash
# Check count
docker exec regulens-db psql -U regulens_user -d regulens -c "SELECT COUNT(*) FROM clients;"
# Expected: 100

# Check sample data
docker exec regulens-db psql -U regulens_user -d regulens -c "SELECT name, entity_type, ca_nexus, tx_nexus, array_length(tax_credits_used, 1) FROM clients LIMIT 5;"
# Expected: Data matches CSV

# Check specific client
docker exec regulens-db psql -U regulens_user -d regulens -c "SELECT name, tax_credits_used FROM clients WHERE name = 'TECH_001';"
# Expected: TECH_001 with tax_credits_used = {R&D}
```

### 4. Test Idempotency
```bash
# Run import again
python scripts/import_clients.py data/sample/client_profiles_mvp.csv

# Expected: "Skipped (existing): 100", "Successfully inserted: 0"
```

### 5. Test Force Reimport
```bash
# Force reimport
python scripts/import_clients.py data/sample/client_profiles_mvp.csv --force
# Type "yes" when prompted

# Expected: "Deleted 100 existing clients", "Successfully inserted: 100"
```

### 6. Run Test Suite
```bash
# Run all import tests
uv run pytest tests/test_import_clients.py -v

# Expected: 20-25 tests passing

# Run with coverage
uv run pytest tests/test_import_clients.py --cov=scripts.import_clients
```

### 7. Test Error Handling
```bash
# Test with non-existent file
python scripts/import_clients.py nonexistent.csv
# Expected: "ERROR: CSV file not found"

# Test with database stopped
docker-compose stop postgres
python scripts/import_clients.py data/sample/client_profiles_mvp.csv
# Expected: "ERROR: Database connection failed"
docker-compose start postgres
```

---

## Critical Files

**New files to create:**

1. **`scripts/import_clients.py`** (~350 lines)
   - Main import script with all functionality
   - CLI interface, parsing, database operations
   - Error handling and progress logging

2. **`tests/test_import_clients.py`** (~450 lines)
   - Comprehensive test coverage
   - 20-25 tests across 4 test classes
   - Unit and integration tests

**Files to reference:**

3. **`backend/app/models/client.py`**
   - Client model definition (field names and types)
   - Required vs optional fields

4. **`backend/app/database.py`**
   - SessionLocal for database connections
   - Connection pattern to follow

5. **`data/sample/client_profiles_mvp.csv`**
   - Source data (100 client profiles)
   - Column names and data format

6. **`tests/test_models.py`**
   - test_db fixture to reuse
   - Bulk insert test pattern reference

---

## Implementation Time Estimate

- **Step 1-2:** Parsing functions (2-3 hours)
- **Step 3:** Database operations (2-3 hours)
- **Step 4-5:** CLI and main function (2 hours)
- **Step 6:** Testing (3-4 hours)
- **Verification:** Manual testing (1 hour)
- **Total:** 10-13 hours

---

## Success Criteria

After implementation:

1. ✅ Script imports all 100 clients successfully
2. ✅ Boolean conversion works correctly
3. ✅ Tax credits array parsing works
4. ✅ Idempotency verified (second run skips all)
5. ✅ Force mode deletes and reimports
6. ✅ All tests passing (20-25 tests)
7. ✅ Clear error messages for failures
8. ✅ Database contains 100 clients with correct data
9. ✅ Can query clients by state nexus for scraper testing
8. `tax_credits_used` - ARRAY(String), default=list (use `list` not `[]` to avoid mutable default)
9. `created_at` - DateTime(timezone=True), server_default=func.now()
10. `updated_at` - DateTime(timezone=True), onupdate=func.now(), nullable=True

**Relationship:**
```python
alerts = relationship("Alert", back_populates="client")
```

**Table name:** `"clients"`

---

### Step 2: Create Publication Model

**File:** `backend/app/models/publication.py` (NEW)

**Required imports:**
```python
from backend.app.database import Base
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
```

**8 Fields to implement:**
1. `id` - UUID(as_uuid=True), primary_key, default=uuid.uuid4
2. `title` - String, nullable=False
3. `state` - String, nullable=False (CA, TX, FL)
4. `source` - String, nullable=False (e.g., "CA FTB Newsroom")
5. `url` - String, nullable=False
6. `content` - Text, nullable=True (full text or summary)
7. `published_date` - DateTime(timezone=True), nullable=True
8. `scraped_at` - DateTime(timezone=True), server_default=func.now()
9. `processed` - Boolean, default=False (AI processing status)

**Relationship:**
```python
alerts = relationship("Alert", back_populates="publication")
```

**Table name:** `"publications"`

---

### Step 3: Create Alert Model

**File:** `backend/app/models/alert.py` (NEW)

**Required imports:**
```python
from backend.app.database import Base
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
```

**13 Fields to implement:**
1. `id` - UUID(as_uuid=True), primary_key, default=uuid.uuid4
2. `publication_id` - UUID(as_uuid=True), ForeignKey('publications.id'), nullable=False
3. `client_id` - UUID(as_uuid=True), ForeignKey('clients.id'), nullable=False
4. `summary` - Text, nullable=True (2-3 sentence AI summary)
5. `affects_client` - String, nullable=True (YES, MAYBE, NO)
6. `impact_level` - String, nullable=True (HIGH, MEDIUM, LOW)
7. `explanation` - Text, nullable=True (why this affects the client)
8. `action_items` - ARRAY(String), nullable=True (what client should do)
9. `reasoning` - Text, nullable=True (AI reasoning for audit trail)
10. `email_sent` - Boolean, default=False
11. `reviewed` - Boolean, default=False
12. `created_at` - DateTime(timezone=True), server_default=func.now()

**Relationships (bidirectional):**
```python
publication = relationship("Publication", back_populates="alerts")
client = relationship("Client", back_populates="alerts")
```

**Table name:** `"alerts"`

**Critical:** Import order matters - Alert depends on both Client and Publication being imported first.

---

### Step 4: Update models/__init__.py

**File:** `backend/app/models/__init__.py`

Replace current content with:
```python
"""
SQLAlchemy database models for ReguLens.

Models:
- Client: Tax client profiles
- Publication: Regulatory publications from state agencies
- Alert: AI-generated alerts matching publications to clients
"""

from backend.app.database import Base
from backend.app.models.client import Client
from backend.app.models.publication import Publication
from backend.app.models.alert import Alert

__all__ = [
    "Base",
    "Client",
    "Publication",
    "Alert",
]
```

---

### Step 5: Initialize Alembic

**Command:**
```bash
alembic init alembic
```

**Expected output:**
- Creates `alembic/` directory with `env.py`, `script.py.mako`, `versions/`
- Creates `alembic.ini` configuration file

---

### Step 6: Configure Alembic

**File:** `alembic.ini` (line ~58-60)

Comment out the hardcoded sqlalchemy.url:
```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
# Use programmatic config in env.py instead
```

**File:** `alembic/env.py`

**Add imports at top (after existing imports):**
```python
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings
from backend.app.database import Base
from backend.app.models import Client, Publication, Alert
```

**Set target_metadata (replace `target_metadata = None`):**
```python
target_metadata = Base.metadata
```

**Configure `run_migrations_offline()` (around line 50):**
```python
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    # ... rest of function
```

**Configure `run_migrations_online()` (around line 70):**
```python
def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import engine_from_config, pool
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # ... rest of function
```

---

### Step 7: Generate and Run Initial Migration

**Generate migration:**
```bash
alembic revision --autogenerate -m "Initial schema with Client, Publication, Alert models"
```

**Expected:** Alembic detects all 3 tables with correct columns, foreign keys, and types.

**Review migration file** in `alembic/versions/` to verify:
- CREATE TABLE clients (11 columns)
- CREATE TABLE publications (8 columns)
- CREATE TABLE alerts (13 columns)
- Foreign keys: alerts.publication_id → publications.id, alerts.client_id → clients.id
- Correct types: UUID, String, Boolean, DateTime(timezone=True), Text, ARRAY(String)

**Run migration:**
```bash
alembic upgrade head
```

**Expected:** Creates tables in PostgreSQL database.

---

### Step 8: Create Comprehensive Test Suite

**File:** `tests/test_models.py` (NEW)

**Test database fixture:**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import Client, Publication, Alert

@pytest.fixture(scope="function")
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    TestSessionLocal = sessionmaker(bind=engine)
    db = TestSessionLocal()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(engine)
```

**Test classes to implement (25-30 tests total):**

1. **TestClientModel** - Client instantiation, defaults, UUID generation
   - `test_create_client_minimal()` - Required fields only
   - `test_create_client_full()` - All fields populated
   - `test_client_uuid_uniqueness()` - UUIDs are unique
   - `test_client_nexus_defaults()` - Boolean defaults work
   - `test_client_tax_credits_default()` - Array defaults to empty list

2. **TestPublicationModel** - Publication instantiation and defaults
   - `test_create_publication_minimal()`
   - `test_publication_processed_default()` - Defaults to False
   - `test_publication_scraped_at_auto()` - Timestamp auto-generated

3. **TestAlertModel** - Alert instantiation and foreign keys
   - `test_create_alert_minimal()`
   - `test_alert_defaults()` - email_sent, reviewed default to False

4. **TestModelRelationships** - Relationship queries
   - `test_client_publication_alert_relationship()` - Complete chain
   - `test_alert_client_relationship()` - Many-to-one works
   - `test_alert_publication_relationship()` - Many-to-one works
   - `test_client_alerts_collection()` - One-to-many works
   - `test_publication_alerts_collection()` - One-to-many works

5. **TestDatabaseOperations** - CRUD and queries
   - `test_query_clients_by_nexus()` - Filter by state
   - `test_query_alerts_by_impact()` - Filter by impact level
   - `test_bulk_insert_clients()` - Bulk operations for CSV import

6. **TestEdgeCases** - Nullable fields, long text, constraints
   - `test_nullable_fields_accept_none()`
   - `test_empty_array_default()`
   - `test_long_text_fields()` - Text fields handle large content
   - `test_foreign_key_constraint_violation()` - FK validation works

---

## Verification Steps

### 1. Verify Model Imports
```bash
# Test that models can be imported
uv run python -c "from backend.app.models import Client, Publication, Alert; print('✓ Models imported successfully')"

# Expected output: ✓ Models imported successfully
```

### 2. Verify Database Tables Created
```bash
# Check PostgreSQL tables exist
docker exec -it regulens-db psql -U regulens_user -d regulens -c "\dt"

# Expected output shows 4 tables:
# - clients
# - publications  
# - alerts
# - alembic_version
```

### 3. Inspect Table Schema
```bash
# Check clients table structure
docker exec -it regulens-db psql -U regulens_user -d regulens -c "\d clients"

# Verify: 11 columns with correct types (uuid, varchar, boolean, timestamp, text[])

# Check alerts table foreign keys
docker exec -it regulens-db psql -U regulens_user -d regulens -c "\d alerts"

# Verify foreign keys:
# - alerts_client_id_fkey → clients(id)
# - alerts_publication_id_fkey → publications(id)
```

### 4. Run Test Suite
```bash
# Run all model tests
uv run pytest tests/test_models.py -v

# Expected: 25-30 tests pass
# Expected coverage: All model files tested

# Run with coverage
uv run pytest tests/test_models.py --cov=backend.app.models --cov-report=term-missing
```

### 5. Test Database Operations (Manual)
```bash
# Create test script to verify CRUD operations
uv run python -c "
from backend.app.database import SessionLocal
from backend.app.models import Client

db = SessionLocal()
try:
    # Create test client
    client = Client(
        name='TEST_001',
        entity_type='C-Corp',
        industry='Technology',
        revenue_range='1-10M',
        ca_nexus=True
    )
    db.add(client)
    db.commit()
    
    # Query it back
    found = db.query(Client).filter(Client.name == 'TEST_001').first()
    print(f'✓ Client created and queried: {found.name}, ID: {found.id}')
    
    # Clean up
    db.delete(found)
    db.commit()
    print('✓ Test client cleaned up')
finally:
    db.close()
"
```

### 6. Verify Alembic State
```bash
# Check current migration version
uv run alembic current

# Expected: Shows migration hash and "Initial schema with Client, Publication, Alert models"

# Check migration history
uv run alembic history

# Expected: Shows 1 migration (head)

---

## Acceptance Criteria Checklist

**Model Implementation:**
- [ ] `backend/app/models/client.py` created with all 11 fields
- [ ] `backend/app/models/publication.py` created with all 8 fields  
- [ ] `backend/app/models/alert.py` created with all 13 fields
- [ ] All models inherit from `Base` from `backend.app.database`
- [ ] UUID fields use `UUID(as_uuid=True)` type
- [ ] Boolean fields have appropriate defaults (False)
- [ ] ARRAY fields use PostgreSQL ARRAY type with `default=list`
- [ ] DateTime fields use `DateTime(timezone=True)`
- [ ] Timestamps use `server_default=func.now()` where needed

**Relationships:**
- [ ] Alert has `publication` and `client` relationships
- [ ] Publication has `alerts` back_populates relationship
- [ ] Client has `alerts` back_populates relationship
- [ ] Foreign keys use correct UUID column types
- [ ] Relationships are bidirectional

**Exports and Imports:**
- [ ] `backend/app/models/__init__.py` exports all three models
- [ ] Models can be imported: `from backend.app.models import Client, Publication, Alert`

**Alembic Setup:**
- [ ] Alembic initialized with `alembic init alembic`
- [ ] `alembic/env.py` configured to import models and use settings.DATABASE_URL
- [ ] Initial migration generated with `alembic revision --autogenerate`
- [ ] Migration reviewed and contains all 3 tables with correct schema
- [ ] Migration applied successfully with `alembic upgrade head`

**Database Verification:**
- [ ] Tables created in PostgreSQL: clients, publications, alerts, alembic_version
- [ ] Foreign key constraints exist on alerts table
- [ ] Can query tables via psql or database client

**Testing:**
- [ ] `tests/test_models.py` created with 25-30 tests
- [ ] Test database fixture configured (SQLite in-memory)
- [ ] Tests cover instantiation, relationships, CRUD operations, edge cases
- [ ] All tests passing with pytest
- [ ] No import errors or circular dependency issues

---

## Critical Files

**New Files to Create:**

1. **`backend/app/models/client.py`** (~60 lines)
   - Client model with 11 fields
   - Relationship to Alert
   - Docstrings and `__repr__`

2. **`backend/app/models/publication.py`** (~50 lines)
   - Publication model with 8 fields
   - Relationship to Alert
   - Docstrings and `__repr__`

3. **`backend/app/models/alert.py`** (~60 lines)
   - Alert model with 13 fields
   - Relationships to Client and Publication
   - Foreign keys
   - Docstrings and `__repr__`

4. **`tests/test_models.py`** (~400-500 lines)
   - Test database fixture
   - 6 test classes
   - 25-30 test methods
   - Comprehensive coverage

**Files to Modify:**

5. **`backend/app/models/__init__.py`** (replace ~13 lines)
   - Import all three models
   - Export in `__all__` list

6. **`alembic/env.py`** (modify ~20 lines)
   - Add sys.path configuration
   - Import models and settings
   - Set target_metadata
   - Configure database URL in offline/online functions

**Generated Files:**

7. **`alembic/versions/<hash>_initial_schema.py`** (auto-generated)
   - Created by `alembic revision --autogenerate`
   - Review before running upgrade

**Directories to Create:**

8. **`alembic/`** - Created by `alembic init alembic`
   - Contains env.py, script.py.mako, versions/

---

## Implementation Time Estimate

- **Model creation (3 files)**: 45-60 minutes
- **models/__init__.py update**: 5 minutes
- **Alembic initialization and configuration**: 20-30 minutes
- **Migration generation and review**: 15 minutes
- **Test suite creation**: 90-120 minutes
- **Testing and verification**: 20-30 minutes
- **Total**: 3-4 hours

---

## Success Criteria

After implementation:

1. ✅ **All three models created** following exact MVP-PLAN.md schema
2. ✅ **Alembic migrations working** with initial schema applied to PostgreSQL
3. ✅ **Database tables created** with correct columns, types, and foreign keys
4. ✅ **Comprehensive test coverage** with 25-30 passing tests
5. ✅ **Models can be imported** from `backend.app.models` without errors
6. ✅ **Relationships work bidirectionally** between Client, Publication, Alert
7. ✅ **Ready for next features**: CSV client import, scrapers, AI matching
