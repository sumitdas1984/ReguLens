"""
Pydantic schemas for Alert model.
"""

from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class AlertResponse(BaseModel):
    """Schema for Alert API response."""

    id: UUID
    publication_id: UUID
    client_id: UUID
    summary: Optional[str] = None
    affects_client: Optional[str] = None
    impact_level: Optional[str] = None
    explanation: Optional[str] = None
    action_items: Optional[List[str]] = []
    reasoning: Optional[str] = None
    email_sent: bool = False
    reviewed: bool = False
    created_at: datetime

    # Include related data for convenience
    client_name: Optional[str] = None
    publication_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("action_items", mode="before")
    @classmethod
    def convert_none_to_empty_list(cls, v):
        """Convert None to empty list for action_items."""
        return v if v is not None else []
