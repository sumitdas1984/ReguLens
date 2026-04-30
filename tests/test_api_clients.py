"""
Tests for /api/clients endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Client


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """Clean the database before each test."""
    db = SessionLocal()
    try:
        # Delete in correct order due to foreign key constraints
        from backend.app.models import Alert, Publication
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
def sample_clients():
    """Create sample clients for testing."""
    db = SessionLocal()
    try:
        clients = [
            Client(
                name=f"TEST_{i:03d}",
                entity_type="C-Corp",
                industry="Technology",
                revenue_range="1-10M",
                ca_nexus=True,
                tx_nexus=False,
                fl_nexus=False,
            )
            for i in range(1, 6)
        ]
        db.bulk_save_objects(clients)
        db.commit()
        return clients
    finally:
        db.close()


class TestListClientsEndpoint:
    """Test GET /api/clients endpoint."""

    def test_list_clients_default_pagination(self, api_client, sample_clients):
        """Test endpoint returns clients with default pagination."""
        response = api_client.get("/api/clients")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "clients" in data
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["clients"]) == 5

    def test_list_clients_custom_limit(self, api_client, sample_clients):
        """Test custom limit parameter."""
        response = api_client.get("/api/clients?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert len(data["clients"]) <= 2

    def test_list_clients_with_offset(self, api_client, sample_clients):
        """Test offset parameter."""
        response = api_client.get("/api/clients?limit=2&offset=2")

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 2
        assert len(data["clients"]) <= 2

    def test_list_clients_limit_too_high(self, api_client):
        """Test limit > 100 returns 422 validation error."""
        response = api_client.get("/api/clients?limit=150")
        assert response.status_code == 422

    def test_list_clients_negative_limit(self, api_client):
        """Test negative limit returns 422 validation error."""
        response = api_client.get("/api/clients?limit=-1")
        assert response.status_code == 422

    def test_list_clients_negative_offset(self, api_client):
        """Test negative offset returns 422 validation error."""
        response = api_client.get("/api/clients?offset=-1")
        assert response.status_code == 422

    def test_list_clients_empty_database(self, api_client):
        """Test endpoint with empty database."""
        # Database is already cleaned by autouse fixture
        response = api_client.get("/api/clients")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["clients"] == []

    def test_list_clients_response_schema(self, api_client, sample_clients):
        """Test response includes all required fields."""
        response = api_client.get("/api/clients?limit=1")

        assert response.status_code == 200
        data = response.json()

        assert len(data["clients"]) == 1
        client = data["clients"][0]

        required_fields = [
            "id",
            "name",
            "entity_type",
            "industry",
            "ca_nexus",
            "tx_nexus",
            "fl_nexus",
            "revenue_range",
            "tax_credits_used",
            "created_at",
        ]
        for field in required_fields:
            assert field in client

    def test_list_clients_offset_beyond_total(self, api_client, sample_clients):
        """Test offset beyond total returns empty list."""
        response = api_client.get("/api/clients?offset=1000")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # Total count is still correct
        assert data["clients"] == []  # But no clients returned
