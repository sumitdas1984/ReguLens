# Spec for API Endpoints

branch: claude/feature/api-endpoints

## Summary
Create basic FastAPI read-only REST endpoints to list clients, publications, and alerts. These endpoints provide the JSON API layer needed for the dashboard and external integrations in the ReguLens MVP.

This feature implements three core GET endpoints:
- `GET /api/clients` - List all client profiles
- `GET /api/publications` - List recent regulatory publications
- `GET /api/alerts` - List recent AI-generated alerts

All endpoints include pagination support and follow RESTful conventions.

## Functional Requirements

### Endpoint Structure
- **Base path:** `/api/` for all API endpoints
- **Response format:** JSON with Pydantic schema validation
- **Pagination:** Query parameters `limit` (default: 50, max: 100) and `offset` (default: 0)
- **HTTP methods:** GET only (read-only endpoints for MVP)
- **Status codes:** 200 OK, 400 Bad Request, 500 Internal Server Error

### GET /api/clients
**Purpose:** Return list of all client profiles

**Query Parameters:**
- `limit` (int, optional): Number of results to return (default: 50, max: 100)
- `offset` (int, optional): Number of results to skip (default: 0)

**Response Schema:**
```json
{
  "total": 100,
  "limit": 50,
  "offset": 0,
  "clients": [
    {
      "id": "uuid",
      "name": "TECH_001",
      "entity_type": "C-Corp",
      "industry": "Software Publishing",
      "industry_naics": "511210",
      "ca_nexus": true,
      "tx_nexus": true,
      "fl_nexus": false,
      "revenue_range": "10-50M",
      "tax_credits_used": ["R&D"],
      "created_at": "2026-05-01T00:00:00Z",
      "updated_at": "2026-05-01T00:00:00Z"
    }
  ]
}
```

### GET /api/publications
**Purpose:** Return list of recent regulatory publications

**Query Parameters:**
- `limit` (int, optional): Number of results to return (default: 50, max: 100)
- `offset` (int, optional): Number of results to skip (default: 0)
- `state` (str, optional): Filter by state (CA, TX, FL)
- `processed` (bool, optional): Filter by processing status

**Response Schema:**
```json
{
  "total": 25,
  "limit": 50,
  "offset": 0,
  "publications": [
    {
      "id": "uuid",
      "title": "New Tax Credit Announced for R&D",
      "state": "CA",
      "source": "CA FTB Newsroom",
      "url": "https://...",
      "content": "Full text...",
      "published_date": "2026-04-30T00:00:00Z",
      "scraped_at": "2026-05-01T08:00:00Z",
      "processed": true
    }
  ]
}
```

### GET /api/alerts
**Purpose:** Return list of recent AI-generated alerts

**Query Parameters:**
- `limit` (int, optional): Number of results to return (default: 50, max: 100)
- `offset` (int, optional): Number of results to skip (default: 0)
- `client_id` (uuid, optional): Filter by specific client
- `impact_level` (str, optional): Filter by impact level (HIGH, MEDIUM, LOW)
- `reviewed` (bool, optional): Filter by review status

**Response Schema:**
```json
{
  "total": 15,
  "limit": 50,
  "offset": 0,
  "alerts": [
    {
      "id": "uuid",
      "publication_id": "uuid",
      "client_id": "uuid",
      "client_name": "TECH_001",
      "publication_title": "New Tax Credit Announced",
      "summary": "Brief summary...",
      "affects_client": "YES",
      "impact_level": "HIGH",
      "explanation": "Why this affects the client...",
      "action_items": ["Review eligibility", "File by deadline"],
      "reasoning": "AI reasoning...",
      "email_sent": true,
      "reviewed": false,
      "created_at": "2026-05-01T08:05:00Z"
    }
  ]
}
```

### API Documentation
- **OpenAPI/Swagger UI:** Accessible at `http://localhost:8000/docs`
- **ReDoc:** Accessible at `http://localhost:8000/redoc`
- FastAPI auto-generates documentation from Pydantic schemas

### Route Registration
- Create route modules in `backend/app/api/` directory
- Register routes in `backend/app/main.py` with `/api` prefix
- Use FastAPI APIRouter for modular route organization

## Possible Edge Cases

### Pagination
- `limit` > 100 → clamp to 100 (don't error)
- `limit` < 1 → return 400 Bad Request
- `offset` < 0 → return 400 Bad Request
- `offset` > total records → return empty list (not error)
- Missing pagination params → use defaults

### Database Queries
- Empty database → return empty list with total=0
- Database connection failure → return 500 with error message
- Invalid UUID in filter (client_id) → return 400 Bad Request
- Slow queries with large datasets → ensure proper indexing

### Data Validation
- Invalid state filter (not CA/TX/FL) → return 400 Bad Request
- Invalid impact_level filter → return 400 Bad Request
- Invalid boolean value for processed/reviewed → return 400 Bad Request
- SQL injection attempts → protected by SQLAlchemy ORM

### Response Formatting
- NULL values in database → serialize as `null` in JSON
- Datetime fields → serialize as ISO 8601 strings with timezone
- Empty arrays → return `[]` not `null`
- UUIDs → serialize as strings

## Acceptance Criteria

### Endpoints Created
- [ ] `GET /api/clients` endpoint implemented
- [ ] `GET /api/publications` endpoint implemented
- [ ] `GET /api/alerts` endpoint implemented
- [ ] All routes registered in main.py with `/api` prefix

### Functionality
- [ ] Endpoints return correct data from database
- [ ] Pagination works (limit and offset)
- [ ] Filter parameters work (state, client_id, impact_level, etc.)
- [ ] Response includes total count, limit, and offset
- [ ] Empty database returns empty list (not error)

### Schema Validation
- [ ] Pydantic response schemas created for all endpoints
- [ ] Schemas include all model fields
- [ ] Datetime fields serialize as ISO 8601 strings
- [ ] UUIDs serialize as strings
- [ ] Arrays serialize correctly

### Error Handling
- [ ] Invalid pagination params return 400 Bad Request
- [ ] Database errors return 500 Internal Server Error
- [ ] Invalid filter values return 400 Bad Request
- [ ] Error responses include helpful messages

### API Documentation
- [ ] OpenAPI docs accessible at `/docs`
- [ ] All endpoints documented with descriptions
- [ ] Query parameters documented
- [ ] Response schemas visible in docs
- [ ] Example requests/responses shown

### Testing
- [ ] Test each endpoint returns data
- [ ] Test pagination works correctly
- [ ] Test filters work correctly
- [ ] Test empty database returns empty list
- [ ] Test invalid parameters return 400
- [ ] Test endpoints accessible at correct paths

## Open Questions

- Should we add sorting parameters (sort_by, sort_order)?
- Should we include related data in responses (e.g., client details in alerts)?
- Should we add a GET /api/clients/{id} endpoint for individual client details?
- Should we implement rate limiting for these endpoints?
- Should we add CORS configuration for frontend access?
- Should we cache responses to reduce database load?

## Testing Guidelines

Create test file(s) in the ./tests folder for the new API endpoints, and create meaningful tests for the following cases, without going too heavy:

### Unit Tests (test_api_clients.py, test_api_publications.py, test_api_alerts.py)
- Test each endpoint returns correct data structure
- Test pagination parameters work correctly
- Test filter parameters work correctly
- Test response schema validation
- Test empty database returns empty list
- Test invalid parameters return 400 errors

### Integration Tests
- Test endpoints with actual database data
- Test pagination with large datasets (>100 records)
- Test multiple filters combined
- Test related data is loaded correctly (joins)
- Test database connection errors are handled

### Edge Cases
- Test limit > 100 is clamped
- Test offset beyond total returns empty list
- Test invalid UUID format in filters
- Test invalid enum values in filters
- Test NULL values in database serialize correctly

### API Documentation Tests
- Test OpenAPI schema is generated correctly
- Test /docs endpoint is accessible
- Test endpoint descriptions are present
