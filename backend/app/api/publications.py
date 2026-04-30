"""
API endpoints for publications.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Optional

from backend.app.database import get_db
from backend.app.models import Publication
from backend.app.schemas import PublicationResponse

router = APIRouter(prefix="/publications", tags=["publications"])


@router.get("", response_model=Dict)
async def list_publications(
    limit: int = Query(default=50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    state: Optional[str] = Query(default=None, pattern="^(CA|TX|FL)$", description="Filter by state (CA, TX, FL)"),
    processed: Optional[bool] = Query(default=None, description="Filter by processing status"),
    db: Session = Depends(get_db),
):
    """
    List regulatory publications with pagination and filters.

    - **limit**: Number of results (1-100, default 50)
    - **offset**: Number of results to skip (default 0)
    - **state**: Filter by state (CA, TX, FL)
    - **processed**: Filter by processing status

    Returns a paginated list of publications with total count.
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
            query.order_by(Publication.scraped_at.desc()).offset(offset).limit(limit).all()
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
