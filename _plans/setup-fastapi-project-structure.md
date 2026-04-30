# Implementation Plan: Setup FastAPI Project Structure

## Context

This plan implements the initial FastAPI project structure for ReguLens MVP - an AI-powered regulatory monitoring platform. The structure provides a foundation for:
- Web scraping regulatory sources (CA, TX, FL)
- AI-powered client matching
- Background job scheduling
- Email alerts
- Minimal dashboard UI

**Current State:**
- Clean project with `uv init` completed
- `pyproject.toml` exists with Python 3.13+ requirement
- Empty dependencies array ready for packages
- MVP-PLAN.md and MVP-ARCHITECTURE.md define requirements
- No backend code structure exists yet

**Goal:** Create directory structure, add core dependencies, and establish minimal working FastAPI app that satisfies all acceptance criteria.

---

## Implementation Steps

### Step 1: Create Directory Structure

Create all required directories and Python package files:

```bash
# Main application structure
mkdir -p backend/app/{models,schemas,api,routes,scrapers,ai,jobs,utils}
mkdir -p backend/{templates,static/{css,js,images}}
mkdir -p scripts
mkdir -p tests

# Create __init__.py for all Python packages
touch backend/app/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/api/__init__.py
touch backend/app/routes/__init__.py
touch backend/app/scrapers/__init__.py
touch backend/app/ai/__init__.py
touch backend/app/jobs/__init__.py
touch backend/app/utils/__init__.py
touch tests/__init__.py

# Preserve empty directories in git
touch backend/templates/.gitkeep
touch backend/static/css/.gitkeep
touch backend/static/js/.gitkeep
touch backend/static/images/.gitkeep
```

**Directory Purpose:**
- `backend/` - Container for all backend code and assets
- `backend/app/` - Main Python package (FastAPI application)
- `backend/app/models/` - SQLAlchemy database models
- `backend/app/schemas/` - Pydantic schemas for validation
- `backend/app/api/` - RESTful JSON API endpoints
- `backend/app/routes/` - HTML dashboard routes (Jinja2)
- `backend/app/scrapers/` - Web scraping modules (4 sources)
- `backend/app/ai/` - AI/LLM integration (Claude API)
- `backend/app/jobs/` - Background job definitions (APScheduler)
- `backend/app/utils/` - Utility functions
- `backend/templates/` - Jinja2 HTML templates
- `backend/static/` - CSS, JavaScript, images
- `scripts/` - Standalone utility scripts
- `tests/` - Test suite

### Step 2: Add Dependencies to pyproject.toml

Add all required dependencies for MVP using uv:

```bash
# Web Framework
uv add "fastapi[standard]==0.115.0"
uv add "uvicorn[standard]==0.34.0"

# Database
uv add "sqlalchemy==2.0.36"
uv add "alembic==1.14.0"
uv add "psycopg2-binary==2.9.10"

# Configuration & Validation
uv add "pydantic==2.10.3"
uv add "pydantic-settings==2.6.1"
uv add "python-dotenv==1.0.1"

# Web Scraping
uv add "playwright==1.49.1"
uv add "beautifulsoup4==4.12.3"
uv add "lxml==5.3.0"

# AI Integration
uv add "anthropic==0.42.0"

# Background Jobs
uv add "apscheduler==3.10.4"

# Email Service
uv add "resend==2.6.0"

# HTTP Client
uv add "httpx==0.28.1"

# Development Dependencies
uv add --dev "pytest==8.3.4"
uv add --dev "pytest-asyncio==0.24.0"
```

Then install Playwright browsers for web scraping:
```bash
playwright install chromium
```

**Why These Dependencies:**
- **fastapi[standard]**: Includes Pydantic, Starlette, and standard extras
- **uvicorn[standard]**: ASGI server with websockets and watchfiles
- **sqlalchemy + alembic**: ORM and database migrations
- **psycopg2-binary**: PostgreSQL driver (binary for easy install)
- **pydantic-settings**: Environment variable management
- **playwright + beautifulsoup4 + lxml**: Web scraping stack
- **anthropic**: Claude API for AI matching
- **apscheduler**: Background job scheduling
- **resend**: Email delivery service
- **pytest + pytest-asyncio**: Testing framework for async code

### Step 3: Create Core Application Files

**File: `backend/app/__init__.py`**
```python
"""
ReguLens Backend Application
AI-powered regulatory monitoring platform
"""

__version__ = "0.1.0"
```

**File: `backend/app/main.py`** (FastAPI entry point)
```python
"""
FastAPI application entry point for ReguLens MVP.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Initialize FastAPI app
app = FastAPI(
    title="ReguLens",
    description="AI-powered regulatory monitoring for tax professionals",
    version="0.1.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="backend/templates")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "ReguLens API is running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Detailed health check for monitoring."""
    return {
        "status": "healthy",
        "service": "regulens-backend",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
```

**File: `backend/app/config.py`** (Configuration management)
```python
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
```

**File: `backend/app/database.py`** (Database connection)
```python
"""
Database connection and session management.
Uses SQLAlchemy for ORM and connection pooling.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database sessions in FastAPI routes.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**File: `backend/app/dependencies.py`** (Dependency injection)
```python
"""
Dependency injection for FastAPI routes.
Centralizes common dependencies like database sessions, config, etc.
"""

from backend.app.database import get_db
from backend.app.config import settings

# Re-export for convenience
__all__ = ["get_db", "get_settings"]


def get_settings():
    """
    Dependency for accessing application settings.
    
    Usage:
        @app.get("/config")
        def get_config(settings = Depends(get_settings)):
            return {"app_name": settings.APP_NAME}
    """
    return settings
```

**Module `__init__.py` files** (Create with docstrings for each subdirectory):

- `backend/app/models/__init__.py`: "SQLAlchemy database models. Models will be added in subsequent features."
- `backend/app/schemas/__init__.py`: "Pydantic schemas for request/response validation."
- `backend/app/api/__init__.py`: "API endpoint definitions."
- `backend/app/routes/__init__.py`: "HTML route handlers for dashboard UI."
- `backend/app/scrapers/__init__.py`: "Web scraping modules for regulatory sources."
- `backend/app/ai/__init__.py`: "AI/LLM integration for document analysis."
- `backend/app/jobs/__init__.py`: "Background job definitions."
- `backend/app/utils/__init__.py`: "Utility functions and helpers."
- `tests/__init__.py`: "Test suite for ReguLens backend."

### Step 4: Create Environment Configuration

**File: `.env.example`** (Template for developers)
```bash
# ReguLens Environment Configuration
# Copy this file to .env and fill in the values

# Application
APP_NAME=ReguLens
APP_VERSION=0.1.0
DEBUG=true

# Database (local PostgreSQL for MVP)
DATABASE_URL=postgresql://regulens_user:regulens_pass@localhost:5432/regulens

# Alert Configuration (MVP - single recipient)
ALERT_RECIPIENT_EMAIL=your-email@example.com
ALERT_RECIPIENT_NAME=Tax Professional (MVP)

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
RESEND_API_KEY=re_...

# Scraping Configuration
SCRAPE_SCHEDULE_HOUR=8
SCRAPE_TIMEOUT_SECONDS=30
```

**Note:** Verify `.gitignore` already excludes `.env` (it does based on exploration).

### Step 5: Create Test Files

**File: `tests/test_structure.py`**
```python
"""
Test that project structure is correctly set up.
Validates acceptance criteria from spec.
"""

import importlib
import pytest
from pathlib import Path


def test_backend_app_directory_exists():
    """Test that backend/app directory exists."""
    app_dir = Path("backend/app")
    assert app_dir.exists()
    assert app_dir.is_dir()


def test_all_required_directories_exist():
    """Test that all required subdirectories exist."""
    required_dirs = [
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/api",
        "backend/app/routes",
        "backend/app/scrapers",
        "backend/app/ai",
        "backend/app/jobs",
        "backend/app/utils",
        "backend/templates",
        "backend/static",
        "scripts",
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        assert path.exists(), f"Directory {dir_path} does not exist"
        assert path.is_dir(), f"{dir_path} is not a directory"


def test_main_module_can_be_imported():
    """Test that backend.app.main can be imported successfully."""
    try:
        from backend.app import main
        assert hasattr(main, "app")
        assert main.app is not None
    except ImportError as e:
        pytest.fail(f"Failed to import backend.app.main: {e}")


def test_fastapi_app_instance_exists():
    """Test that FastAPI app instance can be accessed."""
    from backend.app.main import app
    from fastapi import FastAPI
    
    assert isinstance(app, FastAPI)
    assert app.title == "ReguLens"


def test_all_submodules_can_be_imported():
    """Test that all created modules can be imported."""
    modules = [
        "backend.app",
        "backend.app.config",
        "backend.app.database",
        "backend.app.dependencies",
        "backend.app.models",
        "backend.app.schemas",
        "backend.app.api",
        "backend.app.routes",
        "backend.app.scrapers",
        "backend.app.ai",
        "backend.app.jobs",
        "backend.app.utils",
    ]
    
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_config_loads_from_env():
    """Test that config can be loaded from settings."""
    from backend.app.config import settings
    
    assert settings.APP_NAME == "ReguLens"
    assert settings.APP_VERSION == "0.1.0"
```

**File: `tests/test_api.py`**
```python
"""
Test FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create FastAPI test client."""
    from backend.app.main import app
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns success."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_check_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "regulens-backend"
```

### Step 6: Create Documentation

**File: `backend/README.md`**
```markdown
# ReguLens Backend

FastAPI-based backend for ReguLens MVP - AI-powered regulatory monitoring platform.

## Project Structure

```
backend/
├── app/                      # Main application package
│   ├── main.py               # FastAPI entry point
│   ├── config.py             # Configuration management
│   ├── database.py           # Database connection
│   ├── dependencies.py       # Dependency injection
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── api/                  # API endpoints
│   ├── routes/               # HTML route handlers
│   ├── scrapers/             # Web scraping modules
│   ├── ai/                   # AI/LLM integration
│   ├── jobs/                 # Background jobs
│   └── utils/                # Utility functions
├── templates/                # Jinja2 HTML templates
└── static/                   # CSS, JS, assets
```

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or manually install
uv pip install -e .
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your configuration:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials and API keys.

### 4. Run the Development Server

```bash
# Using uvicorn directly
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py file
python -m backend.app.main
```

The API will be available at:
- Application: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Alternative API Docs (ReDoc): http://localhost:8000/redoc

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code (install ruff first: uv add --dev ruff)
ruff format .

# Lint code
ruff check .
```

## Dependency Management

This project uses `uv` with `pyproject.toml` for dependency management.

To add a new dependency:

```bash
# Production dependency
uv add package-name

# Development dependency
uv add --dev package-name
```

## API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
```

**File: `scripts/README.md`**
```markdown
# ReguLens Utility Scripts

This directory contains standalone utility scripts for ReguLens.

## Future Scripts

- `import_clients.py`: Import client profiles from CSV to database
- `run_scraper.py`: Manually trigger a scraper run
- `test_email.py`: Test email configuration

## Development Guidelines

- Scripts should be standalone (not dependent on FastAPI app running)
- Use argparse for command-line arguments
- Include docstrings and usage examples
- Handle errors gracefully with clear messages
```

---

## Verification Steps

After implementation, verify all acceptance criteria:

### 1. Directory Structure
```bash
# Check all directories exist
ls -la backend/app/
ls -la backend/templates/
ls -la backend/static/
ls -la scripts/
ls -la tests/
```

### 2. Import Test
```bash
# Test that FastAPI app can be imported
python -c "from backend.app.main import app; print('✓ Import successful')"
```

### 3. Run Test Suite
```bash
# Run all tests
pytest tests/ -v

# Expected: All tests pass
```

### 4. Start Development Server
```bash
# Start the FastAPI server
uvicorn backend.app.main:app --reload
```

### 5. Test Endpoints
```bash
# Test health check endpoint
curl http://localhost:8000/

# Expected: {"status":"ok","message":"ReguLens API is running","version":"0.1.0"}

curl http://localhost:8000/health

# Expected: {"status":"healthy","service":"regulens-backend","version":"0.1.0"}
```

### 6. Check API Documentation
Open in browser:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

### 7. Verify Dependencies
```bash
# Check that all dependencies are installed
uv pip list | grep fastapi
uv pip list | grep sqlalchemy
uv pip list | grep playwright
```

---

## Acceptance Criteria Checklist

- [ ] Project structure matches specification in MVP-PLAN.md
- [ ] All required directories exist with proper organization
- [ ] FastAPI application in `backend/app/main.py` can be imported successfully
- [ ] Python can resolve imports from all created modules
- [ ] Dependencies managed via `pyproject.toml` using uv
- [ ] Dependencies can be installed using `uv sync`
- [ ] FastAPI server starts without errors
- [ ] Health check endpoints return 200 OK
- [ ] Test suite passes completely
- [ ] Directory structure is clean, logical, and follows FastAPI best practices

---

## Critical Files

The following files are essential for this implementation:

- `pyproject.toml` - Dependencies and project metadata (updated)
- `backend/app/main.py` - FastAPI application entry point
- `backend/app/config.py` - Configuration management
- `backend/app/database.py` - Database connection setup
- `backend/app/dependencies.py` - Dependency injection
- `.env.example` - Environment variable template
- `tests/test_structure.py` - Structure validation tests
- `tests/test_api.py` - API endpoint tests
- `backend/README.md` - Backend documentation
- `scripts/README.md` - Scripts documentation
