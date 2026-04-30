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
