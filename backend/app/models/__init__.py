"""
SQLAlchemy database models for ReguLens.

Models:
- Client: Tax client profiles
- Publication: Regulatory publications from state agencies
- Alert: AI-generated alerts matching publications to clients
"""

from backend.app.database import Base
from backend.app.models.client import Client
from backend.app.models.publication import Publication
from backend.app.models.alert import Alert

__all__ = [
    "Base",
    "Client",
    "Publication",
    "Alert",
]
