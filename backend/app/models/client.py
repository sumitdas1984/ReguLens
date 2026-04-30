"""
Client database model.

Represents tax professional's clients who are monitored for regulatory changes.
"""

from backend.app.database import Base
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid


class Client(Base):
    """
    Client profile for regulatory monitoring.

    Stores information about tax clients including entity type, industry,
    state nexus, revenue range, and tax credits used. Used by AI matching
    to determine which regulations affect which clients.
    """

    __tablename__ = "clients"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    name = Column(String, nullable=False)  # Client code (e.g., TECH_001)
    entity_type = Column(String, nullable=False)  # C-Corp, S-Corp, LLC, Partnership, Sole Prop
    industry = Column(String, nullable=False)
    industry_naics = Column(String, nullable=True)  # NAICS code (optional)

    # State nexus flags (determines which state regulations apply)
    ca_nexus = Column(Boolean, default=False)  # California nexus
    tx_nexus = Column(Boolean, default=False)  # Texas nexus
    fl_nexus = Column(Boolean, default=False)  # Florida nexus

    # Financial and tax information
    revenue_range = Column(String, nullable=False)  # <1M, 1-10M, 10-50M, 50M+
    tax_credits_used = Column(ARRAY(String), default=list)  # [R&D, Film, Other]

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    alerts = relationship("Alert", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, entity_type={self.entity_type})>"
