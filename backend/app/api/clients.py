"""
API endpoints for clients.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict

from backend.app.database import get_db
from backend.app.models import Client
from backend.app.schemas import ClientResponse

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=Dict)
async def list_clients(
    limit: int = Query(default=50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """
    List all client profiles with pagination.

    - **limit**: Number of results (1-100, default 50)
    - **offset**: Number of results to skip (default 0)

    Returns a paginated list of client profiles with total count.
    """
    try:
        # Get total count
        total = db.query(Client).count()

        # Get paginated results
        clients = db.query(Client).offset(offset).limit(limit).all()

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
