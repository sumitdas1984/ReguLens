"""
Publication database model.

Represents regulatory publications scraped from state tax agency websites.
"""

from backend.app.database import Base
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid


class Publication(Base):
    """
    Regulatory publication from state tax agencies.

    Stores publications scraped from government websites (CA FTB, TX Comptroller,
    FL DOR). Each publication is analyzed by AI to match against client profiles.
    """

    __tablename__ = "publications"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Publication metadata
    title = Column(String, nullable=False)
    state = Column(String, nullable=False)  # CA, TX, FL
    source = Column(String, nullable=False)  # e.g., "CA FTB Newsroom"
    url = Column(String, nullable=False)

    # Content
    content = Column(Text, nullable=True)  # Full text or summary

    # Timestamps
    published_date = Column(DateTime(timezone=True), nullable=True)  # When agency published
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())  # When we scraped

    # Processing status
    processed = Column(Boolean, default=False)  # Has AI processing completed?

    # Relationships
    alerts = relationship("Alert", back_populates="publication")

    def __repr__(self):
        return f"<Publication(id={self.id}, title={self.title[:50]}, state={self.state})>"
