# Implementation Plan: REST API Endpoints

## Context

This plan implements three read-only REST API endpoints to list clients, publications, and alerts with pagination and filtering support.

**Why this change is needed:**
- The database models and data (100 clients) are in place from PRs #36 and #37
- The MVP needs a JSON API layer for the dashboard and external integrations
- Current FastAPI app only has health check endpoints - no data access API
- These endpoints enable frontend development and external tool integration
- OpenAPI documentation will be auto-generated for easy API exploration

**Current State:**
- ✅ FastAPI app initialized in `backend/app/main.py`
- ✅ Database models exist: Client, Publication, Alert (in `backend/app/models/`)
- ✅ Database session pattern established (`get_db()` dependency)
- ✅ Test patterns established (`test_api.py` with TestClient)
- ✅ 100 sample clients loaded in database
- ❌ No Pydantic response schemas exist (schemas/ directory is empty)
- ❌ No API routers exist (api/ directory is empty)
- ❌ No `/api` routes registered in main.py

**Goal:** Create three GET endpoints (`/api/clients`, `/api/publications`, `/api/alerts`) with pagination, filtering, and comprehensive tests.

---

## Implementation Steps

### Step 1: Create Pydantic Response Schemas

**Location:** `backend/app/schemas/`

#### File: `backend/app/schemas/client.py` (NEW, ~40 lines)

Create schemas for Client responses:

```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class ClientResponse(BaseModel):
    """Schema for Client API response."""
    id: UUID
    name: str
    entity_type: str
    industry: str
    industry_naics: Optional[str] = None
    ca_nexus: bool
    tx_nexus: bool
    fl_nexus: bool
    revenue_range: str
    tax_credits_used: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
```

**Key points:**
- Use `ConfigDict(from_attributes=True)` for SQLAlchemy ORM compatibility
- UUIDs will serialize as strings automatically
- Datetimes will serialize as ISO 8601 strings
- Arrays default to empty list if None

#### File: `backend/app/schemas/publication.py` (NEW, ~35 lines)

```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class PublicationResponse(BaseModel):
    """Schema for Publication API response."""
    id: UUID
    title: str
    state: str
    source: str
    url: str
    content: Optional[str] = None
    published_date: Optional[datetime] = None
    scraped_at: datetime
    processed: bool = False

    model_config = ConfigDict(from_attributes=True)
```

#### File: `backend/app/schemas/alert.py` (NEW, ~45 lines)

```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class AlertResponse(BaseModel):
    """Schema for Alert API response."""
    id: UUID
    publication_id: UUID
    client_id: UUID
    summary: Optional[str] = None
    affects_client: Optional[str] = None
    impact_level: Optional[str] = None
    explanation: Optional[str] = None
    action_items: List[str] = []
    reasoning: Optional[str] = None
    email_sent: bool = False
    reviewed: bool = False
    created_at: datetime
    
    # Include related data for convenience
    client_name: Optional[str] = None
    publication_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
```

**Note:** Alert schema includes `client_name` and `publication_title` for convenience (will be populated via joins).

#### File: `backend/app/schemas/__init__.py` (MODIFY)

Update to export all schemas:
```python
from backend.app.schemas.client import ClientResponse
from backend.app.schemas.publication import PublicationResponse
from backend.app.schemas.alert import AlertResponse

__all__ = [
    "ClientResponse",
    "PublicationResponse",
    "AlertResponse",
]
```

---

### Step 2: Create Pagination Response Wrapper

**File:** `backend/app/schemas/pagination.py` (NEW, ~25 lines)

Create a generic pagination wrapper:

```python
from pydantic import BaseModel
from typing import List, TypeVar, Generic

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    total: int
    limit: int
    offset: int
    items: List[T]

    model_config = {"arbitrary_types_allowed": True}
```

**Usage:** This allows type-safe responses like `PaginatedResponse[ClientResponse]`.

Update `schemas/__init__.py` to export it.

---

### Step 3: Create API Router for Clients

**File:** `backend/app/api/clients.py` (NEW, ~80 lines)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.database import get_db
from backend.app.models import Client
from backend.app.schemas import ClientResponse

router = APIRouter(prefix="/clients", tags=["clients"])

@router.get("", response_model=dict)
async def list_clients(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List all client profiles with pagination.
    
    - **limit**: Number of results (1-100, default 50)
    - **offset**: Number of results to skip (default 0)
    """
    try:
        # Get total count
        total = db.query(Client).count()
        
        # Get paginated results
        clients = (
            db.query(Client)
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        # Convert to response schemas
        client_data = [ClientResponse.model_validate(c) for c in clients]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "clients": client_data,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
```

**Key implementation details:**
- Use `Query(ge=1, le=100)` for automatic validation (FastAPI handles 400 errors)
- Separate query for total count (efficient)
- `model_validate()` converts SQLAlchemy models to Pydantic schemas
- Exception handling for database errors

---

### Step 4: Create API Router for Publications

**File:** `backend/app/api/publications.py` (NEW, ~100 lines)

Similar structure to clients.py but with additional filters:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.database import get_db
from backend.app.models import Publication
from backend.app.schemas import PublicationResponse

router = APIRouter(prefix="/publications", tags=["publications"])

@router.get("", response_model=dict)
async def list_publications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    state: Optional[str] = Query(default=None, regex="^(CA|TX|FL)$"),
    processed: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    List regulatory publications with pagination and filters.
    
    - **limit**: Number of results (1-100, default 50)
    - **offset**: Number of results to skip (default 0)
    - **state**: Filter by state (CA, TX, FL)
    - **processed**: Filter by processing status
    """
    try:
        # Build query with filters
        query = db.query(Publication)
        
        if state:
            query = query.filter(Publication.state == state)
        
        if processed is not None:
            query = query.filter(Publication.processed == processed)
        
        # Get total count
        total = query.count()
        
        # Get paginated results (order by scraped_at descending)
        publications = (
            query
            .order_by(Publication.scraped_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        # Convert to response schemas
        pub_data = [PublicationResponse.model_validate(p) for p in publications]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "publications": pub_data,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
```

**Key features:**
- `regex="^(CA|TX|FL)$"` validates state parameter (FastAPI returns 400 for invalid)
- Order by `scraped_at DESC` to show recent publications first
- Filters are optional - apply only if provided

---

### Step 5: Create API Router for Alerts

**File:** `backend/app/api/alerts.py` (NEW, ~120 lines)

Most complex endpoint with joins and multiple filters:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from uuid import UUID

from backend.app.database import get_db
from backend.app.models import Alert, Client, Publication
from backend.app.schemas import AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=dict)
async def list_alerts(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    client_id: Optional[UUID] = Query(default=None),
    impact_level: Optional[str] = Query(default=None, regex="^(HIGH|MEDIUM|LOW)$"),
    reviewed: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    List AI-generated alerts with pagination and filters.
    
    - **limit**: Number of results (1-100, default 50)
    - **offset**: Number of results to skip (default 0)
    - **client_id**: Filter by specific client UUID
    - **impact_level**: Filter by impact (HIGH, MEDIUM, LOW)
    - **reviewed**: Filter by review status
    """
    try:
        # Build query with eager loading of relationships
        query = (
            db.query(Alert)
            .join(Client, Alert.client_id == Client.id)
            .join(Publication, Alert.publication_id == Publication.id)
            .options(joinedload(Alert.client), joinedload(Alert.publication))
        )
        
        # Apply filters
        if client_id:
            query = query.filter(Alert.client_id == client_id)
        
        if impact_level:
            query = query.filter(Alert.impact_level == impact_level)
        
        if reviewed is not None:
            query = query.filter(Alert.reviewed == reviewed)
        
        # Get total count
        total = query.count()
        
        # Get paginated results (order by created_at descending)
        alerts = (
            query
            .order_by(Alert.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        # Convert to response schemas with related data
        alert_data = []
        for alert in alerts:
            alert_dict = AlertResponse.model_validate(alert).model_dump()
            alert_dict["client_name"] = alert.client.name
            alert_dict["publication_title"] = alert.publication.title
            alert_data.append(alert_dict)
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "alerts": alert_data,
        }
    
    except ValueError as e:
        # Invalid UUID format
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
```

**Key features:**
- Uses `joinedload()` for efficient eager loading of relationships
- Manually adds `client_name` and `publication_title` from relationships
- UUID validation handled automatically by FastAPI/Pydantic
- Multiple optional filters

---

### Step 6: Register API Routers in Main App

**File:** `backend/app/main.py` (MODIFY, add ~15 lines)

Add API router registration after the existing health check routes:

```python
# Add near top with other imports
from backend.app.api import clients, publications, alerts

# Add after existing route definitions (after @app.get("/health"))
# Register API routers with /api prefix
app.include_router(clients.router, prefix="/api")
app.include_router(publications.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
```

**Result:** Routes will be available at:
- `GET /api/clients`
- `GET /api/publications`
- `GET /api/alerts`

---

### Step 7: Create API Router __init__.py

**File:** `backend/app/api/__init__.py` (MODIFY, ~10 lines)

Export routers for easy import:

```python
"""
API routers for REST endpoints.
"""

from backend.app.api import clients, publications, alerts

__all__ = [
    "clients",
    "publications",
    "alerts",
]
```

---

### Step 8: Create Comprehensive API Tests

**File:** `tests/test_api_clients.py` (NEW, ~150 lines)

```python
"""Tests for /api/clients endpoint."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import Client
from tests.test_models import test_db


@pytest.fixture
def api_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_clients(test_db):
    """Create sample clients for testing."""
    clients = [
        Client(
            name=f"TEST_{i:03d}",
            entity_type="C-Corp",
            industry="Technology",
            revenue_range="1-10M",
            ca_nexus=True,
            tx_nexus=False,
            fl_nexus=False,
        )
        for i in range(1, 6)
    ]
    test_db.bulk_save_objects(clients)
    test_db.commit()
    return clients


class TestListClientsEndpoint:
    """Test GET /api/clients endpoint."""
    
    def test_list_clients_default_pagination(self, api_client, sample_clients):
        """Test endpoint returns clients with default pagination."""
        response = api_client.get("/api/clients")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "clients" in data
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["clients"]) == 5
    
    def test_list_clients_custom_limit(self, api_client, sample_clients):
        """Test custom limit parameter."""
        response = api_client.get("/api/clients?limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert len(data["clients"]) <= 2
    
    def test_list_clients_with_offset(self, api_client, sample_clients):
        """Test offset parameter."""
        response = api_client.get("/api/clients?limit=2&offset=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 2
        assert len(data["clients"]) <= 2
    
    def test_list_clients_limit_validation(self, api_client):
        """Test limit > 100 returns 422 validation error."""
        response = api_client.get("/api/clients?limit=150")
        assert response.status_code == 422  # Validation error
    
    def test_list_clients_negative_offset(self, api_client):
        """Test negative offset returns 422 validation error."""
        response = api_client.get("/api/clients?offset=-1")
        assert response.status_code == 422
    
    def test_list_clients_empty_database(self, api_client, test_db):
        """Test endpoint with empty database."""
        # Ensure database is empty
        test_db.query(Client).delete()
        test_db.commit()
        
        response = api_client.get("/api/clients")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["clients"] == []
    
    def test_list_clients_response_schema(self, api_client, sample_clients):
        """Test response includes all required fields."""
        response = api_client.get("/api/clients?limit=1")
        
        assert response.status_code == 200
        data = response.json()
        
        client = data["clients"][0]
        required_fields = [
            "id", "name", "entity_type", "industry", 
            "ca_nexus", "tx_nexus", "fl_nexus", 
            "revenue_range", "tax_credits_used", 
            "created_at"
        ]
        for field in required_fields:
            assert field in client
```

**Similar test files:**
- `tests/test_api_publications.py` - Tests for publications endpoint with state/processed filters
- `tests/test_api_alerts.py` - Tests for alerts endpoint with client_id/impact_level/reviewed filters

**Test coverage goals:**
- Default pagination behavior
- Custom limit/offset
- Validation errors (limit > 100, negative offset)
- Empty database
- Filter parameters
- Response schema validation

---

## Verification Steps

### 1. Verify Schemas Import Correctly
```bash
uv run python -c "from backend.app.schemas import ClientResponse, PublicationResponse, AlertResponse; print('✓ Schemas imported')"
```

### 2. Start FastAPI Server
```bash
uv run uvicorn backend.app.main:app --reload
```

### 3. Test Endpoints Manually

**Check OpenAPI docs:**
```bash
# Browser: http://localhost:8000/docs
# Should show three new endpoints under "clients", "publications", "alerts" tags
```

**Test GET /api/clients:**
```bash
curl http://localhost:8000/api/clients
curl "http://localhost:8000/api/clients?limit=10&offset=0"
```

**Test GET /api/publications:**
```bash
curl http://localhost:8000/api/publications
curl "http://localhost:8000/api/publications?state=CA&processed=false"
```

**Test GET /api/alerts:**
```bash
curl http://localhost:8000/api/alerts
curl "http://localhost:8000/api/alerts?impact_level=HIGH&reviewed=false"
```

### 4. Run Test Suite
```bash
# Run all API tests
uv run pytest tests/test_api_clients.py -v
uv run pytest tests/test_api_publications.py -v
uv run pytest tests/test_api_alerts.py -v

# Run all tests together
uv run pytest tests/test_api*.py -v

# Expected: 30-40 tests passing
```

### 5. Verify API Documentation
- Visit `http://localhost:8000/docs`
- Verify all three endpoints are documented
- Verify query parameters are shown
- Try "Try it out" feature for each endpoint
- Verify response schemas are displayed correctly

### 6. Test Edge Cases Manually
```bash
# Invalid limit (should return 422)
curl "http://localhost:8000/api/clients?limit=150"

# Invalid state (should return 422)
curl "http://localhost:8000/api/publications?state=NY"

# Invalid UUID (should return 422)
curl "http://localhost:8000/api/alerts?client_id=invalid-uuid"
```

---

## Critical Files

**New Files to Create:**

1. **`backend/app/schemas/client.py`** (~40 lines)
2. **`backend/app/schemas/publication.py`** (~35 lines)
3. **`backend/app/schemas/alert.py`** (~45 lines)
4. **`backend/app/schemas/pagination.py`** (~25 lines)
5. **`backend/app/api/clients.py`** (~80 lines)
6. **`backend/app/api/publications.py`** (~100 lines)
7. **`backend/app/api/alerts.py`** (~120 lines)
8. **`tests/test_api_clients.py`** (~150 lines)
9. **`tests/test_api_publications.py`** (~180 lines)
10. **`tests/test_api_alerts.py`** (~200 lines)

**Files to Modify:**

11. **`backend/app/schemas/__init__.py`** - Export all schemas
12. **`backend/app/api/__init__.py`** - Export all routers
13. **`backend/app/main.py`** - Register API routers (~15 lines added)

**Total:** ~1,000 new lines of code

---

## Success Criteria

After implementation:

1. ✅ All three endpoints accessible at `/api/clients`, `/api/publications`, `/api/alerts`
2. ✅ Pagination works correctly (limit, offset)
3. ✅ Filters work correctly (state, processed, client_id, impact_level, reviewed)
4. ✅ Response schemas match spec exactly
5. ✅ OpenAPI docs show all endpoints with descriptions
6. ✅ All tests passing (30-40 tests total)
7. ✅ Empty database returns empty list (not error)
8. ✅ Invalid parameters return 422 validation errors
9. ✅ Database errors return 500 with message
10. ✅ UUIDs and datetimes serialize correctly

---

## Implementation Time Estimate

- **Schemas**: 45 minutes (4 files)
- **API Routers**: 90 minutes (3 files with pagination/filtering)
- **Route Registration**: 15 minutes
- **Tests**: 120 minutes (3 test files)
- **Manual Testing**: 30 minutes
- **Documentation Review**: 15 minutes
- **Total**: 4-5 hours
