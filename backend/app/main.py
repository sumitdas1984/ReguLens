"""
FastAPI application entry point for ReguLens MVP.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.app.api import clients, publications, alerts

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


# Register API routers
app.include_router(clients.router, prefix="/api")
app.include_router(publications.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
