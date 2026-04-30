"""
Pydantic schemas for Publication model.
"""

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class PublicationResponse(BaseModel):
    """Schema for Publication API response."""

    id: UUID
    title: str
    state: str
    source: str
    url: str
    content: Optional[str] = None
    published_date: Optional[datetime] = None
    scraped_at: datetime
    processed: bool = False

    model_config = ConfigDict(from_attributes=True)
