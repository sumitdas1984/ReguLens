"""
Comprehensive tests for database models.
Tests model instantiation, relationships, CRUD operations, and edge cases.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.app.database import Base
from backend.app.models import Client, Publication, Alert


@pytest.fixture(scope="function")
def test_db():
    """
    Create test database session using PostgreSQL.

    Uses a transaction that is rolled back after each test to ensure isolation.
    """
    from backend.app.database import engine, SessionLocal

    # Create a connection and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()

    # Create a session bound to the connection
    db = SessionLocal(bind=connection)

    yield db

    # Rollback the transaction to undo all changes
    db.close()
    transaction.rollback()
    connection.close()


class TestClientModel:
    """Test Client model instantiation and defaults."""

    def test_create_client_minimal(self, test_db):
        """Test creating client with required fields only."""
        client = Client(
            name="TEST_001",
            entity_type="C-Corp",
            industry="Technology",
            revenue_range="1-10M"
        )
        test_db.add(client)
        test_db.commit()

        assert client.id is not None  # UUID auto-generated
        assert client.name == "TEST_001"
        assert client.entity_type == "C-Corp"
        assert client.industry == "Technology"
        assert client.revenue_range == "1-10M"
        assert client.ca_nexus is False  # Default
        assert client.tx_nexus is False  # Default
        assert client.fl_nexus is False  # Default
        assert client.tax_credits_used == []  # Default empty list
        assert client.created_at is not None
        assert client.updated_at is None  # Not set on creation

    def test_create_client_full(self, test_db):
        """Test creating client with all fields."""
        client = Client(
            name="TECH_002",
            entity_type="S-Corp",
            industry="Software Publishing",
            industry_naics="541511",
            ca_nexus=True,
            tx_nexus=True,
            fl_nexus=False,
            revenue_range="10-50M",
            tax_credits_used=["R&D", "Film"]
        )
        test_db.add(client)
        test_db.commit()

        assert client.industry_naics == "541511"
        assert client.ca_nexus is True
        assert client.tx_nexus is True
        assert client.fl_nexus is False
        assert client.tax_credits_used == ["R&D", "Film"]

    def test_client_uuid_uniqueness(self, test_db):
        """Test that client IDs are unique."""
        client1 = Client(name="C1", entity_type="LLC", industry="Test", revenue_range="<1M")
        client2 = Client(name="C2", entity_type="LLC", industry="Test", revenue_range="<1M")

        test_db.add_all([client1, client2])
        test_db.commit()

        assert client1.id != client2.id
        assert client1.id is not None
        assert client2.id is not None

    def test_client_nexus_defaults(self, test_db):
        """Test that nexus flags default to False."""
        client = Client(
            name="TEST",
            entity_type="LLC",
            industry="Test",
            revenue_range="<1M"
        )
        test_db.add(client)
        test_db.commit()

        assert client.ca_nexus is False
        assert client.tx_nexus is False
        assert client.fl_nexus is False

    def test_client_tax_credits_default(self, test_db):
        """Test that tax_credits_used defaults to empty list."""
        client = Client(
            name="TEST",
            entity_type="LLC",
            industry="Test",
            revenue_range="<1M"
        )
        test_db.add(client)
        test_db.commit()

        assert client.tax_credits_used == []
        assert isinstance(client.tax_credits_used, list)

    def test_client_repr(self, test_db):
        """Test client string representation."""
        client = Client(
            name="TEST_REP",
            entity_type="C-Corp",
            industry="Tech",
            revenue_range="1-10M"
        )
        test_db.add(client)
        test_db.commit()

        repr_str = repr(client)
        assert "Client" in repr_str
        assert "TEST_REP" in repr_str
        assert "C-Corp" in repr_str


class TestPublicationModel:
    """Test Publication model."""

    def test_create_publication_minimal(self, test_db):
        """Test creating publication with required fields."""
        pub = Publication(
            title="Test Publication",
            state="CA",
            source="CA FTB Newsroom",
            url="https://ftb.ca.gov/test"
        )
        test_db.add(pub)
        test_db.commit()

        assert pub.id is not None
        assert pub.title == "Test Publication"
        assert pub.state == "CA"
        assert pub.source == "CA FTB Newsroom"
        assert pub.url == "https://ftb.ca.gov/test"
        assert pub.processed is False  # Default
        assert pub.scraped_at is not None
        assert pub.content is None  # Nullable
        assert pub.published_date is None  # Nullable

    def test_publication_processed_default(self, test_db):
        """Test that processed defaults to False."""
        pub = Publication(
            title="Test",
            state="TX",
            source="Test",
            url="http://test.com"
        )
        test_db.add(pub)
        test_db.commit()

        assert pub.processed is False

    def test_publication_scraped_at_auto(self, test_db):
        """Test that scraped_at is automatically set."""
        pub = Publication(
            title="Test",
            state="FL",
            source="Test",
            url="http://test.com"
        )
        test_db.add(pub)
        test_db.commit()

        assert pub.scraped_at is not None
        assert isinstance(pub.scraped_at, datetime)

    def test_publication_with_content(self, test_db):
        """Test publication with full content."""
        pub = Publication(
            title="Full Publication",
            state="CA",
            source="CA FTB",
            url="http://test.com",
            content="This is the full content of the publication.",
            published_date=datetime(2026, 4, 30, 12, 0, 0)
        )
        test_db.add(pub)
        test_db.commit()

        assert pub.content == "This is the full content of the publication."
        assert pub.published_date.year == 2026

    def test_publication_repr(self, test_db):
        """Test publication string representation."""
        pub = Publication(
            title="A very long publication title that should be truncated in repr",
            state="TX",
            source="Test",
            url="http://test.com"
        )
        test_db.add(pub)
        test_db.commit()

        repr_str = repr(pub)
        assert "Publication" in repr_str
        assert "TX" in repr_str


class TestAlertModel:
    """Test Alert model."""

    def test_create_alert_minimal(self, test_db):
        """Test creating alert with minimal fields."""
        # Create dependencies
        client = Client(name="C1", entity_type="LLC", industry="Test", revenue_range="<1M")
        pub = Publication(title="P1", state="CA", source="Test", url="http://test.com")
        test_db.add_all([client, pub])
        test_db.commit()

        # Create alert
        alert = Alert(
            publication_id=pub.id,
            client_id=client.id
        )
        test_db.add(alert)
        test_db.commit()

        assert alert.id is not None
        assert alert.publication_id == pub.id
        assert alert.client_id == client.id
        assert alert.email_sent is False  # Default
        assert alert.reviewed is False  # Default
        assert alert.created_at is not None

    def test_alert_defaults(self, test_db):
        """Test that email_sent and reviewed default to False."""
        client = Client(name="C1", entity_type="LLC", industry="Test", revenue_range="<1M")
        pub = Publication(title="P1", state="CA", source="Test", url="http://test.com")
        test_db.add_all([client, pub])
        test_db.commit()

        alert = Alert(publication_id=pub.id, client_id=client.id)
        test_db.add(alert)
        test_db.commit()

        assert alert.email_sent is False
        assert alert.reviewed is False

    def test_alert_with_ai_analysis(self, test_db):
        """Test alert with full AI analysis fields."""
        client = Client(name="C1", entity_type="C-Corp", industry="Tech", revenue_range="10-50M")
        pub = Publication(title="Tax Update", state="CA", source="CA FTB", url="http://test.com")
        test_db.add_all([client, pub])
        test_db.commit()

        alert = Alert(
            publication_id=pub.id,
            client_id=client.id,
            summary="This regulation affects C-Corps in technology sector.",
            affects_client="YES",
            impact_level="HIGH",
            explanation="The new tax credit applies to R&D activities.",
            action_items=["Review R&D expenses", "File amended return"],
            reasoning="Client is C-Corp with tech industry and likely R&D activities."
        )
        test_db.add(alert)
        test_db.commit()

        assert alert.summary is not None
        assert alert.affects_client == "YES"
        assert alert.impact_level == "HIGH"
        assert alert.action_items == ["Review R&D expenses", "File amended return"]

    def test_alert_repr(self, test_db):
        """Test alert string representation."""
        client = Client(name="C1", entity_type="LLC", industry="Test", revenue_range="<1M")
        pub = Publication(title="P1", state="CA", source="Test", url="http://test.com")
        test_db.add_all([client, pub])
        test_db.commit()

        alert = Alert(
            publication_id=pub.id,
            client_id=client.id,
            impact_level="MEDIUM"
        )
        test_db.add(alert)
        test_db.commit()

        repr_str = repr(alert)
        assert "Alert" in repr_str
        assert "MEDIUM" in repr_str


class TestModelRelationships:
    """Test relationships between models."""

    def test_client_publication_alert_relationship(self, test_db):
        """Test complete relationship chain."""
        # Create client
        client = Client(
            name="TEST_CLIENT",
            entity_type="C-Corp",
            industry="Tech",
            revenue_range="10-50M",
            ca_nexus=True
        )

        # Create publication
        pub = Publication(
            title="CA Tax Update",
            state="CA",
            source="CA FTB",
            url="https://example.com"
        )

        test_db.add_all([client, pub])
        test_db.commit()

        # Create alert
        alert = Alert(
            publication_id=pub.id,
            client_id=client.id,
            summary="Test summary",
            affects_client="YES",
            impact_level="HIGH"
        )

        test_db.add(alert)
        test_db.commit()

        # Test relationships
        assert alert.client.name == "TEST_CLIENT"
        assert alert.publication.title == "CA Tax Update"
        assert len(client.alerts) == 1
        assert len(pub.alerts) == 1
        assert client.alerts[0].id == alert.id
        assert pub.alerts[0].id == alert.id

    def test_alert_client_relationship(self, test_db):
        """Test many-to-one relationship from Alert to Client."""
        client = Client(name="C1", entity_type="LLC", industry="Test", revenue_range="<1M")
        pub = Publication(title="P1", state="CA", source="Test", url="http://test.com")
        test_db.add_all([client, pub])
        test_db.commit()

        alert = Alert(publication_id=pub.id, client_id=client.id)
        test_db.add(alert)
        test_db.commit()

        # Access client through alert
        assert alert.client is not None
        assert alert.client.name == "C1"

    def test_alert_publication_relationship(self, test_db):
        """Test many-to-one relationship from Alert to Publication."""
        client = Client(name="C1", entity_type="LLC", industry="Test", revenue_range="<1M")
        pub = Publication(title="Important Update", state="TX", source="Test", url="http://test.com")
        test_db.add_all([client, pub])
        test_db.commit()

        alert = Alert(publication_id=pub.id, client_id=client.id)
        test_db.add(alert)
        test_db.commit()

        # Access publication through alert
        assert alert.publication is not None
        assert alert.publication.title == "Important Update"

    def test_client_alerts_collection(self, test_db):
        """Test one-to-many relationship from Client to Alerts."""
        client = Client(name="MULTI_ALERT", entity_type="C-Corp", industry="Test", revenue_range="1-10M")
        pub1 = Publication(title="P1", state="CA", source="Test", url="http://test1.com")
        pub2 = Publication(title="P2", state="TX", source="Test", url="http://test2.com")
        test_db.add_all([client, pub1, pub2])
        test_db.commit()

        # Create multiple alerts for same client
        alert1 = Alert(publication_id=pub1.id, client_id=client.id, impact_level="HIGH")
        alert2 = Alert(publication_id=pub2.id, client_id=client.id, impact_level="LOW")
        test_db.add_all([alert1, alert2])
        test_db.commit()

        # Access alerts through client
        assert len(client.alerts) == 2
        impact_levels = [a.impact_level for a in client.alerts]
        assert "HIGH" in impact_levels
        assert "LOW" in impact_levels

    def test_publication_alerts_collection(self, test_db):
        """Test one-to-many relationship from Publication to Alerts."""
        client1 = Client(name="C1", entity_type="LLC", industry="Test", revenue_range="<1M")
        client2 = Client(name="C2", entity_type="C-Corp", industry="Test", revenue_range="10-50M")
        pub = Publication(title="Affects Multiple", state="FL", source="Test", url="http://test.com")
        test_db.add_all([client1, client2, pub])
        test_db.commit()

        # Create multiple alerts for same publication
        alert1 = Alert(publication_id=pub.id, client_id=client1.id)
        alert2 = Alert(publication_id=pub.id, client_id=client2.id)
        test_db.add_all([alert1, alert2])
        test_db.commit()

        # Access alerts through publication
        assert len(pub.alerts) == 2
        client_names = [a.client.name for a in pub.alerts]
        assert "C1" in client_names
        assert "C2" in client_names


class TestDatabaseOperations:
    """Test database CRUD operations."""

    def test_query_clients_by_nexus(self, test_db):
        """Test querying clients by state nexus."""
        ca_client = Client(
            name="CA_CLIENT",
            entity_type="C-Corp",
            industry="Tech",
            revenue_range="10-50M",
            ca_nexus=True,
            tx_nexus=False
        )
        tx_client = Client(
            name="TX_CLIENT",
            entity_type="LLC",
            industry="Retail",
            revenue_range="1-10M",
            ca_nexus=False,
            tx_nexus=True
        )

        test_db.add_all([ca_client, tx_client])
        test_db.commit()

        # Query CA clients
        ca_clients = test_db.query(Client).filter(Client.ca_nexus == True).all()
        assert len(ca_clients) == 1
        assert ca_clients[0].name == "CA_CLIENT"

        # Query TX clients
        tx_clients = test_db.query(Client).filter(Client.tx_nexus == True).all()
        assert len(tx_clients) == 1
        assert tx_clients[0].name == "TX_CLIENT"

    def test_query_alerts_by_impact(self, test_db):
        """Test querying alerts by impact level."""
        client = Client(name="C1", entity_type="LLC", industry="Test", revenue_range="<1M")
        pub = Publication(title="P1", state="CA", source="Test", url="http://test.com")
        test_db.add_all([client, pub])
        test_db.commit()

        high_alert = Alert(
            publication_id=pub.id,
            client_id=client.id,
            impact_level="HIGH",
            affects_client="YES"
        )
        low_alert = Alert(
            publication_id=pub.id,
            client_id=client.id,
            impact_level="LOW",
            affects_client="MAYBE"
        )

        test_db.add_all([high_alert, low_alert])
        test_db.commit()

        # Query high impact alerts
        high_alerts = test_db.query(Alert).filter(Alert.impact_level == "HIGH").all()
        assert len(high_alerts) == 1
        assert high_alerts[0].affects_client == "YES"

    def test_bulk_insert_clients(self, test_db):
        """Test bulk inserting clients (for CSV import)."""
        clients = [
            Client(
                name=f"CLIENT_{i:03d}",
                entity_type="LLC",
                industry="Test",
                revenue_range="<1M"
            )
            for i in range(100)
        ]

        test_db.bulk_save_objects(clients)
        test_db.commit()

        count = test_db.query(Client).count()
        assert count == 100


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_nullable_fields_accept_none(self, test_db):
        """Test that nullable fields accept None."""
        pub = Publication(
            title="Test",
            state="CA",
            source="Test",
            url="http://test.com",
            content=None,  # Nullable
            published_date=None  # Nullable
        )
        test_db.add(pub)
        test_db.commit()

        assert pub.content is None
        assert pub.published_date is None

    def test_empty_array_default(self, test_db):
        """Test that array fields default to empty list."""
        client = Client(
            name="TEST",
            entity_type="LLC",
            industry="Test",
            revenue_range="<1M"
            # tax_credits_used not specified
        )
        test_db.add(client)
        test_db.commit()

        assert client.tax_credits_used == []

    def test_long_text_fields(self, test_db):
        """Test that Text fields handle large content."""
        long_text = "A" * 10000  # 10KB text

        pub = Publication(
            title="Test",
            state="CA",
            source="Test",
            url="http://test.com",
            content=long_text
        )
        test_db.add(pub)
        test_db.commit()

        assert len(pub.content) == 10000

    def test_foreign_key_constraint_violation(self, test_db):
        """Test that invalid foreign keys are rejected."""
        import uuid as uuid_module

        # Try to create alert with non-existent publication_id
        alert = Alert(
            publication_id=uuid_module.uuid4(),  # Random UUID not in DB
            client_id=uuid_module.uuid4(),
            summary="Test"
        )
        test_db.add(alert)

        with pytest.raises(IntegrityError):
            test_db.commit()
