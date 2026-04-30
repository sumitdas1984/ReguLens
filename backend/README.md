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

### 3. Setup PostgreSQL Database

The easiest way to run PostgreSQL for local development is using Docker.

#### Option A: Docker Compose (Recommended)

Start the database using the provided `docker-compose.yml`:

```bash
# Start PostgreSQL in background
docker-compose up -d

# Verify it's running
docker-compose ps

# View logs (optional)
docker-compose logs -f postgres
```

**Database connection details:**
- Host: `localhost`
- Port: `5432`
- Database: `regulens`
- User: `regulens_user`
- Password: `regulens_pass`

**Container management:**
```bash
# Stop database (data persists)
docker-compose down

# Stop and remove all data
docker-compose down -v

# Restart database
docker-compose restart postgres

# View database logs
docker-compose logs -f postgres
```

#### Option B: Manual Docker Run

If you prefer to run PostgreSQL without docker-compose:

```bash
docker run --name regulens-db \
  -e POSTGRES_USER=regulens_user \
  -e POSTGRES_PASSWORD=regulens_pass \
  -e POSTGRES_DB=regulens \
  -p 5432:5432 \
  -v regulens-data:/var/lib/postgresql/data \
  -d postgres:16-alpine

# Start/stop
docker start regulens-db
docker stop regulens-db
```

#### Option C: Local PostgreSQL Installation

If you prefer a native installation:

1. **Windows**: Download from https://www.postgresql.org/download/windows/
2. **macOS**: `brew install postgresql@16`
3. **Linux**: `sudo apt install postgresql-16`

Then create the database:

```sql
CREATE DATABASE regulens;
CREATE USER regulens_user WITH PASSWORD 'regulens_pass';
GRANT ALL PRIVILEGES ON DATABASE regulens TO regulens_user;
```

#### Verify Database Connection

Test the connection:

```bash
# Using Docker
docker exec -it regulens-db psql -U regulens_user -d regulens

# Or using psql directly
psql -h localhost -U regulens_user -d regulens

# Inside psql:
\l              # List databases
\dt             # List tables (empty for now)
\q              # Quit
```

### 4. Configure Environment

Copy `.env.example` to `.env` and fill in your configuration:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials and API keys:

```bash
# Database (if using Docker defaults, this is already correct)
DATABASE_URL=postgresql://regulens_user:regulens_pass@localhost:5432/regulens

# API Keys (get these from respective services)
ANTHROPIC_API_KEY=sk-ant-your-key-here
RESEND_API_KEY=re_your-key-here

# Alert Configuration
ALERT_RECIPIENT_EMAIL=your-email@example.com
```

### 5. Initialize Database (Future Step)

Once database models are created, you'll run migrations:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

> **Note**: Database models and migrations will be added in subsequent features. For now, the database connection is configured but no tables exist yet.

### 6. Run the Development Server

```bash
# Using uv run (recommended - uses virtual environment)
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Or activate venv first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py file
uv run python -m backend.app.main
```

The API will be available at:
- **Application**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc

### 7. Verify Everything Works

Quick health check:

```bash
# Test the API
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"regulens-backend","version":"0.1.0"}
```

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

## Troubleshooting

### Database Connection Issues

**Problem**: `FATAL: password authentication failed for user "regulens_user"`

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart the database
docker-compose restart postgres

# Check logs for errors
docker-compose logs postgres

# Verify connection string in .env matches docker-compose.yml
```

**Problem**: `connection refused` or `could not connect to server`

**Solution**:
```bash
# Ensure PostgreSQL is running
docker-compose up -d

# Check if port 5432 is available
netstat -an | grep 5432  # Linux/Mac
netstat -an | findstr 5432  # Windows

# If port is in use, stop other PostgreSQL instances
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'backend'`

**Solution**:
```bash
# Make sure you're running from project root
cd /path/to/ReguLens

# Use uv run to ensure correct environment
uv run python -m backend.app.main

# Or activate virtual environment first
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows
```

### Playwright Issues

**Problem**: `playwright._impl._errors.Error: Executable doesn't exist`

**Solution**:
```bash
# Install Playwright browsers
uv run playwright install chromium

# Or with system playwright
playwright install chromium
```

### Port Already in Use

**Problem**: `Address already in use: 0.0.0.0:8000`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000       # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or use a different port
uvicorn backend.app.main:app --port 8001
```

## Quick Start Summary

```bash
# 1. Install dependencies
uv sync

# 2. Start database
docker-compose up -d

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run server
uv run uvicorn backend.app.main:app --reload

# 5. Open browser
# http://localhost:8000/docs
```
