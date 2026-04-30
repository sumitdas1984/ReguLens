"""
Tests for /api/alerts endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Client, Publication, Alert


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """Clean the database before each test."""
    db = SessionLocal()
    try:
        db.query(Alert).delete()
        db.query(Publication).delete()
        db.query(Client).delete()
        db.commit()
        yield
    finally:
        db.close()


@pytest.fixture
def api_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_data():
    """Create sample clients, publications, and alerts for testing."""
    db = SessionLocal()
    try:
        # Create clients
        client1 = Client(
            name="TEST_001",
            entity_type="C-Corp",
            industry="Technology",
            revenue_range="10-50M",
        )
        client2 = Client(
            name="TEST_002",
            entity_type="LLC",
            industry="Finance",
            revenue_range="1-10M",
        )
        db.add(client1)
        db.add(client2)
        db.commit()

        # Create publications
        pub1 = Publication(
            title="Tax Update 1",
            state="CA",
            source="CA FTB",
            url="https://example.com/1",
        )
        pub2 = Publication(
            title="Tax Update 2",
            state="TX",
            source="TX Comptroller",
            url="https://example.com/2",
        )
        db.add(pub1)
        db.add(pub2)
        db.commit()

        # Create alerts
        alert1 = Alert(
            publication_id=pub1.id,
            client_id=client1.id,
            impact_level="HIGH",
            reviewed=False,
            summary="High impact alert",
        )
        alert2 = Alert(
            publication_id=pub2.id,
            client_id=client2.id,
            impact_level="MEDIUM",
            reviewed=True,
            summary="Medium impact alert",
        )
        alert3 = Alert(
            publication_id=pub1.id,
            client_id=client2.id,
            impact_level="LOW",
            reviewed=False,
            summary="Low impact alert",
        )
        db.add(alert1)
        db.add(alert2)
        db.add(alert3)
        db.commit()

        # Capture IDs before session closes to avoid DetachedInstanceError
        client1_id = client1.id
        client2_id = client2.id

        return {
            "client1_id": client1_id,
            "client2_id": client2_id,
            "clients": [client1, client2],
            "publications": [pub1, pub2],
            "alerts": [alert1, alert2, alert3],
        }
    finally:
        db.close()


class TestListAlertsEndpoint:
    """Test GET /api/alerts endpoint."""

    def test_list_alerts_default(self, api_client, sample_data):
        """Test endpoint returns alerts with default pagination."""
        response = api_client.get("/api/alerts")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "alerts" in data
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["alerts"]) == 3

    def test_list_alerts_includes_related_data(self, api_client, sample_data):
        """Test alerts include client_name and publication_title."""
        response = api_client.get("/api/alerts")

        assert response.status_code == 200
        data = response.json()

        alert = data["alerts"][0]
        assert "client_name" in alert
        assert "publication_title" in alert
        assert alert["client_name"] in ["TEST_001", "TEST_002"]
        assert "Tax Update" in alert["publication_title"]

    def test_list_alerts_filter_by_client_id(self, api_client, sample_data):
        """Test client_id filter parameter."""
        client1_id = sample_data["client1_id"]
        response = api_client.get(f"/api/alerts?client_id={client1_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["client_id"] == str(client1_id)

    def test_list_alerts_filter_by_impact_level(self, api_client, sample_data):
        """Test impact_level filter parameter."""
        response = api_client.get("/api/alerts?impact_level=HIGH")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["impact_level"] == "HIGH"

    def test_list_alerts_filter_by_reviewed(self, api_client, sample_data):
        """Test reviewed filter parameter."""
        response = api_client.get("/api/alerts?reviewed=false")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        for alert in data["alerts"]:
            assert alert["reviewed"] is False

    def test_list_alerts_combined_filters(self, api_client, sample_data):
        """Test combining multiple filters."""
        response = api_client.get("/api/alerts?impact_level=HIGH&reviewed=false")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        alert = data["alerts"][0]
        assert alert["impact_level"] == "HIGH"
        assert alert["reviewed"] is False

    def test_list_alerts_invalid_impact_level(self, api_client):
        """Test invalid impact_level returns 422 validation error."""
        response = api_client.get("/api/alerts?impact_level=CRITICAL")
        assert response.status_code == 422

    def test_list_alerts_invalid_uuid(self, api_client):
        """Test invalid UUID returns 422 validation error."""
        response = api_client.get("/api/alerts?client_id=invalid-uuid")
        assert response.status_code == 422

    def test_list_alerts_pagination(self, api_client, sample_data):
        """Test pagination works with alerts."""
        response = api_client.get("/api/alerts?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert len(data["alerts"]) == 2

    def test_list_alerts_empty_database(self, api_client):
        """Test endpoint with empty database."""
        # Database is already cleaned by autouse fixture
        response = api_client.get("/api/alerts")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["alerts"] == []

    def test_list_alerts_response_schema(self, api_client, sample_data):
        """Test response includes all required fields."""
        response = api_client.get("/api/alerts?limit=1")

        assert response.status_code == 200
        data = response.json()

        alert = data["alerts"][0]
        required_fields = [
            "id",
            "publication_id",
            "client_id",
            "impact_level",
            "reviewed",
            "created_at",
            "client_name",
            "publication_title",
        ]
        for field in required_fields:
            assert field in alert
