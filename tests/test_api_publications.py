"""
Tests for /api/publications endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Publication


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """Clean the database before each test."""
    db = SessionLocal()
    try:
        # Delete in correct order due to foreign key constraints
        from backend.app.models import Alert, Client
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
def sample_publications():
    """Create sample publications for testing."""
    db = SessionLocal()
    try:
        publications = [
            Publication(
                title="CA Tax Update 1",
                state="CA",
                source="CA FTB",
                url="https://example.com/1",
                content="Content 1",
                processed=True,
            ),
            Publication(
                title="TX Tax Update 1",
                state="TX",
                source="TX Comptroller",
                url="https://example.com/2",
                content="Content 2",
                processed=False,
            ),
            Publication(
                title="CA Tax Update 2",
                state="CA",
                source="CA FTB",
                url="https://example.com/3",
                content="Content 3",
                processed=False,
            ),
            Publication(
                title="FL Tax Update 1",
                state="FL",
                source="FL DOR",
                url="https://example.com/4",
                content="Content 4",
                processed=True,
            ),
        ]
        db.bulk_save_objects(publications)
        db.commit()
        return publications
    finally:
        db.close()


class TestListPublicationsEndpoint:
    """Test GET /api/publications endpoint."""

    def test_list_publications_default(self, api_client, sample_publications):
        """Test endpoint returns publications with default pagination."""
        response = api_client.get("/api/publications")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "publications" in data
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["publications"]) == 4

    def test_list_publications_filter_by_state(self, api_client, sample_publications):
        """Test state filter parameter."""
        response = api_client.get("/api/publications?state=CA")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["publications"]) == 2
        for pub in data["publications"]:
            assert pub["state"] == "CA"

    def test_list_publications_filter_by_processed(self, api_client, sample_publications):
        """Test processed filter parameter."""
        response = api_client.get("/api/publications?processed=true")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["publications"]) == 2
        for pub in data["publications"]:
            assert pub["processed"] is True

    def test_list_publications_filter_by_unprocessed(self, api_client, sample_publications):
        """Test unprocessed filter parameter."""
        response = api_client.get("/api/publications?processed=false")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        for pub in data["publications"]:
            assert pub["processed"] is False

    def test_list_publications_combined_filters(self, api_client, sample_publications):
        """Test combining state and processed filters."""
        response = api_client.get("/api/publications?state=CA&processed=false")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["publications"]) == 1
        pub = data["publications"][0]
        assert pub["state"] == "CA"
        assert pub["processed"] is False

    def test_list_publications_invalid_state(self, api_client):
        """Test invalid state returns 422 validation error."""
        response = api_client.get("/api/publications?state=NY")
        assert response.status_code == 422

    def test_list_publications_pagination(self, api_client, sample_publications):
        """Test pagination works with publications."""
        response = api_client.get("/api/publications?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert len(data["publications"]) == 2

    def test_list_publications_empty_database(self, api_client):
        """Test endpoint with empty database."""
        # Database is already cleaned by autouse fixture
        response = api_client.get("/api/publications")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["publications"] == []

    def test_list_publications_response_schema(self, api_client, sample_publications):
        """Test response includes all required fields."""
        response = api_client.get("/api/publications?limit=1")

        assert response.status_code == 200
        data = response.json()

        pub = data["publications"][0]
        required_fields = [
            "id",
            "title",
            "state",
            "source",
            "url",
            "scraped_at",
            "processed",
        ]
        for field in required_fields:
            assert field in pub
