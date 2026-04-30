"""
Pydantic schemas for Client model.
"""

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class ClientResponse(BaseModel):
    """Schema for Client API response."""

    id: UUID
    name: str
    entity_type: str
    industry: str
    industry_naics: Optional[str] = None
    ca_nexus: bool
    tx_nexus: bool
    fl_nexus: bool
    revenue_range: str
    tax_credits_used: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
