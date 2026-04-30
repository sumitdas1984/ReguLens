# Implementation Plan: Database Models (Client, Publication, Alert)

## Context

This plan implements the three core SQLAlchemy ORM models for ReguLens MVP, following the exact database schema defined in `docs/MVP-PLAN.md`.

**Why this change is needed:**
- Database models are the foundation for all ReguLens features (scrapers, AI matching, alerts)
- Client model stores tax professional's client profiles (100 sample clients from CSV)
- Publication model stores scraped regulatory documents from CA/TX/FL agencies
- Alert model links publications to affected clients with AI-generated analysis
- Models enable persistent storage, querying, and relationships between entities

**Current State:**
- ✅ Database setup complete in `backend/app/database.py` (Base class, engine, sessions)
- ✅ Models directory exists at `backend/app/models/` with placeholder `__init__.py`
- ✅ SQLAlchemy 2.0.36 and psycopg2-binary 2.9.10 installed
- ✅ PostgreSQL 16 running via Docker Compose
- ❌ No model files created yet (client.py, publication.py, alert.py)
- ❌ Alembic installed but NOT initialized (no migrations setup)
- ❌ No tests for models

**Goal:** Create three production-ready SQLAlchemy models with proper relationships, set up Alembic migrations, and add comprehensive tests.

---

## Implementation Steps

### Step 1: Create Client Model

**File:** `backend/app/models/client.py` (NEW)

**Required imports:**
```python
from backend.app.database import Base
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
```

**11 Fields to implement:**
1. `id` - UUID(as_uuid=True), primary_key, default=uuid.uuid4
2. `name` - String, nullable=False (client code like TECH_001)
3. `entity_type` - String, nullable=False (C-Corp, S-Corp, LLC, Partnership, Sole Prop)
4. `industry` - String, nullable=False
5. `industry_naics` - String, nullable=True
6. `ca_nexus`, `tx_nexus`, `fl_nexus` - Boolean, default=False (state nexus flags)
7. `revenue_range` - String, nullable=False (<1M, 1-10M, 10-50M, 50M+)
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
```

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
