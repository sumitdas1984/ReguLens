"""
Alert database model.

Represents AI-generated alerts linking publications to affected clients.
"""

from backend.app.database import Base
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid


class Alert(Base):
    """
    AI-generated alert matching publications to clients.

    Created by AI matching process when a publication is determined to affect
    a client. Contains summary, impact analysis, and recommended actions.
    """

    __tablename__ = "alerts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    publication_id = Column(UUID(as_uuid=True), ForeignKey('publications.id'), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), nullable=False)

    # AI analysis results
    summary = Column(Text, nullable=True)  # 2-3 sentence summary
    affects_client = Column(String, nullable=True)  # YES, MAYBE, NO
    impact_level = Column(String, nullable=True)  # HIGH, MEDIUM, LOW
    explanation = Column(Text, nullable=True)  # Why this affects the client
    action_items = Column(ARRAY(String), nullable=True)  # What client should do
    reasoning = Column(Text, nullable=True)  # AI reasoning for audit trail

    # Status tracking
    email_sent = Column(Boolean, default=False)  # Email delivery status
    reviewed = Column(Boolean, default=False)  # User acknowledged in dashboard
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    publication = relationship("Publication", back_populates="alerts")
    client = relationship("Client", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, client_id={self.client_id}, impact={self.impact_level})>"
