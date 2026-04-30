# Spec for Setup FastAPI Project Structure

branch: claude/feature/setup-fastapi-project-structure

## Summary
Create the initial FastAPI project structure with proper directory organization to support the ReguLens MVP. This establishes the foundation for the regulatory monitoring platform with clearly separated concerns for API routes, data models, scrapers, AI processing, and background jobs.

## Functional Requirements
- Create a `backend/` directory as the root for all backend code
- Create `backend/app/` directory containing the main FastAPI application
- Initialize `backend/app/main.py` as the FastAPI application entry point
- Create configuration management file `backend/app/config.py`
- Create database connection file `backend/app/database.py`
- Create dependency injection file `backend/app/dependencies.py`
- Create subdirectories for organizing code:
  - `backend/app/models/` - Database models (SQLAlchemy)
  - `backend/app/schemas/` - Pydantic schemas for request/response validation
  - `backend/app/api/` - API endpoint definitions
  - `backend/app/routes/` - Route handlers
  - `backend/app/scrapers/` - Web scraping modules for regulatory sources
  - `backend/app/ai/` - AI/LLM integration for document analysis
  - `backend/app/jobs/` - Background job definitions
  - `backend/app/utils/` - Utility functions and helpers
- Create `backend/templates/` directory for Jinja2 HTML templates (dashboard UI)
- Create `backend/static/` directory for CSS, JavaScript, and static assets
- Create `scripts/` directory at project root for utility scripts
- Initialize dependency management:
  - Create `requirements.in` for direct dependencies (hand-written)
  - Generate `requirements.txt` for full dependency tree (uv-generated, used for deployment)
  - Use `uv` as the package manager for local development (fast, modern)
  - Ensure `requirements.txt` is maintained for cloud deployment compatibility (Render, Railway, AWS)

## Possible Edge Cases
- Ensure all directories contain `__init__.py` files where needed for proper Python module imports
- Verify that the project structure allows for easy testing and import paths
- Ensure `requirements.txt` stays in sync with `requirements.in` when dependencies change
- Consider if any additional subdirectories are needed for tests alongside the code
- Verify that `uv` commands work correctly on the target development environment (Windows/Linux/macOS)

## Acceptance Criteria
- Project structure matches the specification in MVP-PLAN.md
- All required directories exist with proper organization
- FastAPI application in `backend/app/main.py` can be imported successfully
- Python can resolve imports from all created modules
- Both `requirements.in` and `requirements.txt` files exist at project root
- Dependencies can be installed using `uv pip install -r requirements.txt`
- `requirements.txt` is deployment-ready for cloud platforms (Render/Railway/AWS)
- Directory structure is clean, logical, and follows FastAPI best practices

## Open Questions
- Do we need separate test directories within each module, or a single top-level `tests/` directory?
- Should `__init__.py` files be empty or contain module-level exports?
- Should we include a `.python-version` file to specify the Python version for the project?

## Testing Guidelines
Create test file(s) in the ./tests folder for verifying the project structure:
- Test that all required directories exist
- Test that `backend/app/main.py` can be imported without errors
- Test that Python module resolution works correctly for all subdirectories
- Verify that the FastAPI app instance can be created and accessed
