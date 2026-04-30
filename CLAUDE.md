# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ReguLens** is an AI-powered regulatory monitoring system for tax professionals. It automatically scrapes government tax agency websites (CA, TX, FL), uses Claude AI to match new regulations to client profiles, and sends email alerts when clients are affected.

**Core Mission**: Eliminate the "manual discovery gap" - reduce time from regulation publication to client impact analysis from weeks to minutes.

**Current Phase**: MVP - Local development only (no cloud deployment yet)

## System Architecture

ReguLens follows a **scheduled background processing** architecture, not a real-time system:

```
Daily Schedule (8 AM):
1. Scrapers run → Fetch new publications → Store in DB
2. AI Processor runs (8:05 AM) → Match publications to clients → Create alerts → Send emails
3. Dashboard displays → Recent alerts (last 30 days) → Mark as reviewed
```

### Key Architectural Decisions

1. **Server-Side Rendering (NOT SPA)**
   - FastAPI + Jinja2 templates render HTML on server
   - No React/Vue/Next.js - traditional PHP/Django-style architecture
   - Static files served from `backend/static/`
   - Templates in `backend/templates/`

2. **Monolithic Backend Structure**
   - Single FastAPI app in `backend/app/`
   - Database models: SQLAlchemy ORM
   - Background jobs: APScheduler (not Celery)
   - All async code uses Python asyncio

3. **AI Matching Strategy**
   - Client filtering by state nexus BEFORE AI calls (optimization)
   - Claude API analyzes publication + client context
   - Returns: impact level (High/Medium/Low) + reasoning
   - Each publication-client pair is one API call

4. **Data Flow**
   ```
   Scrapers → Publications table
   Publications + Clients → AI Matcher → Alerts table
   Alerts → Email Service (Resend)
   Alerts → Dashboard (Jinja2 templates)
   ```

## Development Commands

### Environment Setup

```bash
# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Start PostgreSQL
docker-compose up -d

# Configure environment
cp .env.example .env
# Edit .env with API keys
```

### Running the Application

```bash
# Start development server (with hot reload)
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Or using python directly
uv run python -m backend.app.main

# Access API docs
# http://localhost:8000/docs
```

### Testing

```bash
# Run all tests (36 tests total)
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_config.py -v        # 28 config validation tests
uv run pytest tests/test_structure.py -v     # 6 structure tests
uv run pytest tests/test_api.py -v           # 2 API tests

# Run with coverage
uv run pytest --cov=backend --cov-report=html

# Run specific test
uv run pytest tests/test_api.py::test_root_endpoint -v

# Run specific test class
uv run pytest tests/test_config.py::TestDatabaseURLValidation -v
```

### Database Management

```bash
# Create migration (after model changes)
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# Access database directly
docker exec -it regulens-db psql -U regulens_user -d regulens
```

### Docker Database Commands

```bash
# Start database
docker-compose up -d

# Stop database (data persists)
docker-compose down

# View logs
docker-compose logs -f postgres

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

## Code Organization

### Backend Structure

```
backend/app/
├── main.py              # FastAPI app entry point, health endpoints
├── config.py            # Pydantic Settings (loads from .env)
├── database.py          # SQLAlchemy engine, Base, get_db()
├── dependencies.py      # FastAPI dependency injection helpers
├── models/              # SQLAlchemy ORM models (Client, Publication, Alert)
├── schemas/             # Pydantic schemas for API validation
├── api/                 # JSON REST API endpoints (/api/*)
├── routes/              # HTML dashboard routes (/, /dashboard)
├── scrapers/            # Web scraping modules (4 sources)
│   ├── base.py          # Base scraper class
│   ├── ca_ftb_newsroom.py
│   ├── tx_comptroller_pubs.py
│   ├── tx_comptroller_tax.py
│   └── fl_dor_tips.py
├── ai/                  # AI/LLM integration
│   ├── matcher.py       # Publication-to-client matching logic
│   └── summarizer.py    # Publication summarization
├── jobs/                # APScheduler background jobs
│   ├── scheduler.py     # Job scheduler configuration
│   ├── scrape_job.py    # Daily scraping job (8 AM)
│   └── process_job.py   # AI processing job (8:05 AM)
└── utils/               # Utilities
    ├── email.py         # Email sending via Resend
    └── formatting.py    # Email template formatting
```

### Important Patterns

1. **Configuration Management**
   - All config in `backend/app/config.py` using Pydantic Settings v2
   - Configuration validated at startup with field validators:
     - `DATABASE_URL`: Must be valid PostgreSQL connection string
     - `ALERT_RECIPIENT_EMAIL`: Must be valid email format (optional)
     - `ANTHROPIC_API_KEY`: Must start with "sk-ant-" and be 50+ chars (optional)
     - `RESEND_API_KEY`: Must start with "re_" (optional)
     - `SCRAPE_SCHEDULE_HOUR`: Must be 0-23
     - `SCRAPE_TIMEOUT_SECONDS`: Must be positive, max 300 seconds
   - Invalid configuration fails at startup with helpful error messages
   - Never hardcode credentials - use environment variables
   - Access via: `from backend.app.config import settings`
   - Settings is a singleton - same instance everywhere

2. **Database Sessions**
   - Use FastAPI dependency injection: `db: Session = Depends(get_db)`
   - Sessions are automatically closed after request
   - Never create sessions manually

3. **Async/Await**
   - All route handlers should be `async def`
   - Use `asyncio` for concurrent operations
   - Anthropic SDK calls should be awaited

4. **Error Handling**
   - FastAPI automatically converts exceptions to HTTP responses
   - Use `HTTPException` for API errors
   - Configuration errors caught at startup with clear validation messages
   - Log errors to console (no logging framework yet in MVP)

## MVP Constraints

### What's IN Scope
- 4 scrapers: CA FTB Newsroom, TX Comptroller (2 sources), FL DOR TIPs
- 100 sample clients (CSV import, no UI for CRUD)
- Daily scraping schedule (8 AM)
- Claude AI for matching
- Email alerts via Resend
- Read-only dashboard (mark reviewed only)
- Local PostgreSQL database

### What's OUT of Scope (Post-MVP)
- Cloud deployment (runs locally only)
- User authentication/login
- Client profile CRUD UI (CSV import only)
- Additional states beyond CA/TX/FL
- Advanced dashboard features (filters, search, charts)
- Mobile app
- API for external tools

## Key Data Models

### Client
- Entity type, industry (NAICS), state nexus (CA/TX/FL)
- Revenue range, tax credits used
- Loaded from `data/sample/client_profiles_mvp.csv`

### Publication
- Title, date, content, URL, source
- Scraped daily from government websites
- `processed` flag tracks AI analysis status

### Alert
- Links Publication to Client with impact level
- Contains AI reasoning and recommended actions
- `reviewed` flag for dashboard interaction

## External Services

### Required API Keys
1. **Anthropic** (`ANTHROPIC_API_KEY`)
   - Claude Sonnet 4 for AI matching
   - Get from: https://console.anthropic.com/

2. **Resend** (`RESEND_API_KEY`)
   - Transactional email service
   - Get from: https://resend.com/
   - Free tier: 3,000 emails/month

### Database
- PostgreSQL 16 via Docker Compose
- Connection string: `postgresql://regulens_user:regulens_pass@localhost:5432/regulens`
- Data persists in Docker volume `regulens-postgres-data`

## Development Workflow

### Adding a New Scraper
1. Create `backend/app/scrapers/<source_name>.py`
2. Inherit from `BaseScraper` (when created)
3. Implement `scrape()` method returning list of publications
4. Register in APScheduler job
5. Add tests in `tests/test_scrapers.py`

### Adding a Database Model
1. Create model in `backend/app/models/<model_name>.py`
2. Import in `backend/app/models/__init__.py`
3. Create Pydantic schemas in `backend/app/schemas/<model_name>.py`
4. Generate migration: `uv run alembic revision --autogenerate -m "Add <model>"`
5. Apply migration: `uv run alembic upgrade head`

### Adding a Dashboard Page
1. Create HTML template in `backend/templates/<page>.html`
2. Add route in `backend/app/routes/<module>.py`
3. Use Jinja2 template syntax for dynamic content
4. Static assets go in `backend/static/css/` or `backend/static/js/`

## Troubleshooting

### Configuration Validation Errors

If the app fails to start with validation errors:

```bash
# Common issues:

# Invalid DATABASE_URL
# Error: "DATABASE_URL must be a valid PostgreSQL connection string"
# Fix: Ensure format is postgresql://user:pass@host:port/dbname

# Invalid email
# Error: "ALERT_RECIPIENT_EMAIL must be a valid email address"
# Fix: Use valid email format (user@domain.com)

# Invalid API key
# Error: "ANTHROPIC_API_KEY must start with 'sk-ant-'"
# Fix: Check API key from Anthropic Console, ensure complete key copied

# Invalid schedule hour
# Error: "SCRAPE_SCHEDULE_HOUR must be between 0 and 23"
# Fix: Use valid hour (0-23)

# Check current config
uv run python -c "from backend.app.config import settings; print(settings.model_dump())"
```

### Database Connection Refused
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart postgres
```

### Import Errors
```bash
# Always use uv run to ensure correct environment
uv run python <script>

# Or activate venv first
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows
```

### Playwright Browser Not Found
```bash
uv run playwright install chromium
```

### Port 8000 Already in Use
```bash
# Find and kill the process
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Or use different port
uv run uvicorn backend.app.main:app --port 8001
```

## Documentation References

- **MVP Plan**: `docs/MVP-PLAN.md` - Full feature specification
- **Architecture**: `docs/MVP-ARCHITECTURE.md` - System design details
- **Backend Setup**: `backend/README.md` - Detailed setup instructions
- **API Docs**: http://localhost:8000/docs (when server running)
