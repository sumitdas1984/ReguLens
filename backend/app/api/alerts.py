"""
API endpoints for alerts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Dict, Optional
from uuid import UUID

from backend.app.database import get_db
from backend.app.models import Alert, Client, Publication
from backend.app.schemas import AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=Dict)
async def list_alerts(
    limit: int = Query(default=50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    client_id: Optional[UUID] = Query(default=None, description="Filter by specific client UUID"),
    impact_level: Optional[str] = Query(default=None, pattern="^(HIGH|MEDIUM|LOW)$", description="Filter by impact level"),
    reviewed: Optional[bool] = Query(default=None, description="Filter by review status"),
    db: Session = Depends(get_db),
):
    """
    List AI-generated alerts with pagination and filters.

    - **limit**: Number of results (1-100, default 50)
    - **offset**: Number of results to skip (default 0)
    - **client_id**: Filter by specific client UUID
    - **impact_level**: Filter by impact (HIGH, MEDIUM, LOW)
    - **reviewed**: Filter by review status

    Returns a paginated list of alerts with related client and publication data.
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
        alerts = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()

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
