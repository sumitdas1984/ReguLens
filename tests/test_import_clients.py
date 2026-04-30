"""
Tests for CSV client import script.
"""

import csv
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from sqlalchemy.exc import IntegrityError

from scripts.import_clients import (
    parse_boolean,
    parse_tax_credits,
    parse_csv_row,
    read_csv_file,
    check_existing_clients,
    import_clients,
    delete_all_clients,
)
from backend.app.models import Client
from tests.test_models import test_db  # Reuse existing fixture


@pytest.fixture(scope="session", autouse=True)
def clean_database_for_tests():
    """
    Clean the clients table before running tests.

    This ensures tests run in isolation from any existing data.
    Uses session scope so it only runs once at the start of the test session.
    """
    from backend.app.database import SessionLocal

    db = SessionLocal()
    try:
        # Delete all clients before tests run
        db.query(Client).delete()
        db.commit()
        yield
    finally:
        db.close()


class TestParsingFunctions:
    """Test CSV parsing utility functions."""

    def test_parse_boolean_valid_true(self):
        """Test parsing 'True' string."""
        assert parse_boolean("True") is True

    def test_parse_boolean_valid_false(self):
        """Test parsing 'False' string."""
        assert parse_boolean("False") is False

    def test_parse_boolean_empty(self):
        """Test parsing empty string returns False."""
        assert parse_boolean("") is False
        assert parse_boolean(None) is False

    def test_parse_boolean_invalid(self):
        """Test parsing invalid boolean raises ValueError."""
        with pytest.raises(ValueError, match="Invalid boolean value"):
            parse_boolean("YES")

        with pytest.raises(ValueError, match="Invalid boolean value"):
            parse_boolean("1")

        with pytest.raises(ValueError, match="Invalid boolean value"):
            parse_boolean("true")  # lowercase

    def test_parse_tax_credits_multiple(self):
        """Test parsing pipe-delimited tax credits."""
        result = parse_tax_credits("R&D|Other")
        assert result == ["R&D", "Other"]

    def test_parse_tax_credits_single(self):
        """Test parsing single tax credit."""
        result = parse_tax_credits("R&D")
        assert result == ["R&D"]

    def test_parse_tax_credits_empty(self):
        """Test parsing empty tax credits returns empty list."""
        assert parse_tax_credits("") == []
        assert parse_tax_credits("   ") == []

    def test_parse_tax_credits_with_whitespace(self):
        """Test parsing tax credits strips whitespace."""
        result = parse_tax_credits(" R&D | Other | Energy ")
        assert result == ["R&D", "Other", "Energy"]

    def test_parse_csv_row_complete(self):
        """Test parsing CSV row with all fields."""
        row = {
            "name": "TECH_001",
            "entity_type": "C-Corp",
            "industry": "Software Publishing",
            "industry_naics": "511210",
            "ca_nexus": "True",
            "tx_nexus": "False",
            "fl_nexus": "True",
            "revenue_range": "10-50M",
            "tax_credits_used": "R&D|Other",
        }

        client = parse_csv_row(row, row_number=2)

        assert client.name == "TECH_001"
        assert client.entity_type == "C-Corp"
        assert client.industry == "Software Publishing"
        assert client.industry_naics == "511210"
        assert client.ca_nexus is True
        assert client.tx_nexus is False
        assert client.fl_nexus is True
        assert client.revenue_range == "10-50M"
        assert client.tax_credits_used == ["R&D", "Other"]

    def test_parse_csv_row_minimal(self):
        """Test parsing CSV row with only required fields."""
        row = {
            "name": "TEST_001",
            "entity_type": "LLC",
            "industry": "Retail",
            "revenue_range": "<1M",
            "industry_naics": "",
            "ca_nexus": "",
            "tx_nexus": "",
            "fl_nexus": "",
            "tax_credits_used": "",
        }

        client = parse_csv_row(row, row_number=2)

        assert client.name == "TEST_001"
        assert client.entity_type == "LLC"
        assert client.industry == "Retail"
        assert client.revenue_range == "<1M"
        assert client.industry_naics is None
        assert client.ca_nexus is False
        assert client.tx_nexus is False
        assert client.fl_nexus is False
        assert client.tax_credits_used == []

    def test_parse_csv_row_missing_required_field(self):
        """Test parsing row with missing required field raises ValueError."""
        row = {
            "name": "",  # Missing required field
            "entity_type": "LLC",
            "industry": "Retail",
            "revenue_range": "<1M",
        }

        with pytest.raises(ValueError, match="Row 5: Missing required fields: name"):
            parse_csv_row(row, row_number=5)

    def test_parse_csv_row_multiple_missing_fields(self):
        """Test parsing row with multiple missing fields."""
        row = {
            "name": "",
            "entity_type": "",
            "industry": "Retail",
            "revenue_range": "",
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            parse_csv_row(row, row_number=10)

    def test_parse_csv_row_strips_whitespace(self):
        """Test parsing row strips whitespace from fields."""
        row = {
            "name": "  TECH_001  ",
            "entity_type": " C-Corp ",
            "industry": " Software ",
            "revenue_range": " 10-50M ",
        }

        client = parse_csv_row(row, row_number=2)

        assert client.name == "TECH_001"
        assert client.entity_type == "C-Corp"
        assert client.industry == "Software"
        assert client.revenue_range == "10-50M"


class TestReadCSVFile:
    """Test CSV file reading functionality."""

    def test_read_csv_file_success(self):
        """Test reading valid CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "name", "entity_type", "industry", "revenue_range",
                "industry_naics", "ca_nexus", "tx_nexus", "fl_nexus",
                "tax_credits_used"
            ])
            writer.writeheader()
            writer.writerow({
                "name": "TEST_001",
                "entity_type": "LLC",
                "industry": "Retail",
                "revenue_range": "<1M",
                "industry_naics": "",
                "ca_nexus": "True",
                "tx_nexus": "False",
                "fl_nexus": "False",
                "tax_credits_used": "R&D",
            })
            csv_path = Path(f.name)

        try:
            clients = read_csv_file(csv_path)
            assert len(clients) == 1
            assert clients[0].name == "TEST_001"
        finally:
            csv_path.unlink()

    def test_read_csv_file_not_found(self):
        """Test reading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            read_csv_file(Path("nonexistent.csv"))

    def test_read_csv_file_missing_columns(self):
        """Test reading CSV with missing required columns."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "entity_type"])
            writer.writeheader()
            csv_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="CSV missing required columns"):
                read_csv_file(csv_path)
        finally:
            csv_path.unlink()

    def test_read_csv_file_skips_invalid_rows(self, capsys):
        """Test reading CSV skips invalid rows and continues."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "name", "entity_type", "industry", "revenue_range",
                "industry_naics", "ca_nexus", "tx_nexus", "fl_nexus",
                "tax_credits_used"
            ])
            writer.writeheader()
            # Valid row
            writer.writerow({
                "name": "TEST_001",
                "entity_type": "LLC",
                "industry": "Retail",
                "revenue_range": "<1M",
                "industry_naics": "",
                "ca_nexus": "True",
                "tx_nexus": "False",
                "fl_nexus": "False",
                "tax_credits_used": "",
            })
            # Invalid row (missing name)
            writer.writerow({
                "name": "",
                "entity_type": "LLC",
                "industry": "Retail",
                "revenue_range": "<1M",
                "industry_naics": "",
                "ca_nexus": "True",
                "tx_nexus": "False",
                "fl_nexus": "False",
                "tax_credits_used": "",
            })
            csv_path = Path(f.name)

        try:
            clients = read_csv_file(csv_path)
            assert len(clients) == 1  # Only valid row parsed

            # Check warning was printed
            captured = capsys.readouterr()
            assert "WARNING" in captured.out
        finally:
            csv_path.unlink()


class TestDatabaseOperations:
    """Test database operations (uses test_db fixture)."""

    def test_check_existing_clients_none_exist(self, test_db):
        """Test checking for clients when none exist."""
        result = check_existing_clients(test_db, ["CLIENT_001", "CLIENT_002"])
        assert result == {"CLIENT_001": False, "CLIENT_002": False}

    def test_check_existing_clients_some_exist(self, test_db):
        """Test checking for clients when some exist."""
        # Create one client
        client = Client(
            name="CLIENT_001",
            entity_type="LLC",
            industry="Retail",
            revenue_range="<1M"
        )
        test_db.add(client)
        test_db.commit()

        result = check_existing_clients(test_db, ["CLIENT_001", "CLIENT_002"])
        assert result == {"CLIENT_001": True, "CLIENT_002": False}

    def test_check_existing_clients_empty_list(self, test_db):
        """Test checking empty list returns empty dict."""
        result = check_existing_clients(test_db, [])
        assert result == {}

    def test_import_clients_new(self, test_db):
        """Test importing new clients."""
        clients = [
            Client(name="TEST_001", entity_type="LLC", industry="Retail", revenue_range="<1M"),
            Client(name="TEST_002", entity_type="C-Corp", industry="Tech", revenue_range="1-10M"),
        ]

        stats = import_clients(test_db, clients, skip_existing=True, batch_size=50)

        assert stats["total"] == 2
        assert stats["inserted"] == 2
        assert stats["skipped"] == 0
        assert stats["failed"] == 0

        # Verify clients in database
        count = test_db.query(Client).count()
        assert count == 2

    def test_import_clients_skip_existing(self, test_db):
        """Test importing clients skips existing ones."""
        # Create existing client
        existing = Client(
            name="TEST_001",
            entity_type="LLC",
            industry="Retail",
            revenue_range="<1M"
        )
        test_db.add(existing)
        test_db.commit()

        # Try to import including existing client
        clients = [
            Client(name="TEST_001", entity_type="LLC", industry="Retail", revenue_range="<1M"),
            Client(name="TEST_002", entity_type="C-Corp", industry="Tech", revenue_range="1-10M"),
        ]

        stats = import_clients(test_db, clients, skip_existing=True, batch_size=50)

        assert stats["total"] == 2
        assert stats["inserted"] == 1  # Only new client
        assert stats["skipped"] == 1  # Existing client skipped
        assert stats["failed"] == 0

        # Verify only 2 clients in database
        count = test_db.query(Client).count()
        assert count == 2

    def test_import_clients_empty_list(self, test_db):
        """Test importing empty list returns zero stats."""
        stats = import_clients(test_db, [], skip_existing=True, batch_size=50)

        assert stats["total"] == 0
        assert stats["inserted"] == 0
        assert stats["skipped"] == 0
        assert stats["failed"] == 0

    def test_import_clients_batch_processing(self, test_db):
        """Test batch processing with small batch size."""
        clients = [
            Client(name=f"TEST_{i:03d}", entity_type="LLC", industry="Retail", revenue_range="<1M")
            for i in range(5)
        ]

        stats = import_clients(test_db, clients, skip_existing=True, batch_size=2)

        assert stats["inserted"] == 5
        assert test_db.query(Client).count() == 5

    def test_delete_all_clients(self, test_db):
        """Test deleting all clients."""
        # Create some clients
        clients = [
            Client(name="TEST_001", entity_type="LLC", industry="Retail", revenue_range="<1M"),
            Client(name="TEST_002", entity_type="C-Corp", industry="Tech", revenue_range="1-10M"),
            Client(name="TEST_003", entity_type="S-Corp", industry="Finance", revenue_range="10-50M"),
        ]
        test_db.bulk_save_objects(clients)
        test_db.commit()

        # Delete all
        deleted_count = delete_all_clients(test_db)

        assert deleted_count == 3
        assert test_db.query(Client).count() == 0

    def test_delete_all_clients_empty_database(self, test_db):
        """Test deleting from empty database."""
        deleted_count = delete_all_clients(test_db)
        assert deleted_count == 0


class TestIdempotency:
    """Test idempotent import behavior."""

    def test_import_twice_skips_all(self, test_db):
        """Test running import twice skips all clients on second run."""
        clients = [
            Client(name="TEST_001", entity_type="LLC", industry="Retail", revenue_range="<1M"),
            Client(name="TEST_002", entity_type="C-Corp", industry="Tech", revenue_range="1-10M"),
        ]

        # First import
        stats1 = import_clients(test_db, clients, skip_existing=True)
        assert stats1["inserted"] == 2
        assert stats1["skipped"] == 0

        # Second import (same clients)
        clients_copy = [
            Client(name="TEST_001", entity_type="LLC", industry="Retail", revenue_range="<1M"),
            Client(name="TEST_002", entity_type="C-Corp", industry="Tech", revenue_range="1-10M"),
        ]
        stats2 = import_clients(test_db, clients_copy, skip_existing=True)
        assert stats2["inserted"] == 0
        assert stats2["skipped"] == 2

        # Verify still only 2 clients
        assert test_db.query(Client).count() == 2

    def test_partial_import_recovery(self, test_db):
        """Test recovering from partial import."""
        # First import - 3 clients
        clients1 = [
            Client(name="TEST_001", entity_type="LLC", industry="Retail", revenue_range="<1M"),
            Client(name="TEST_002", entity_type="C-Corp", industry="Tech", revenue_range="1-10M"),
            Client(name="TEST_003", entity_type="S-Corp", industry="Finance", revenue_range="10-50M"),
        ]
        stats1 = import_clients(test_db, clients1, skip_existing=True)
        assert stats1["inserted"] == 3

        # Second import - 5 clients (3 existing + 2 new)
        clients2 = [
            Client(name="TEST_001", entity_type="LLC", industry="Retail", revenue_range="<1M"),
            Client(name="TEST_002", entity_type="C-Corp", industry="Tech", revenue_range="1-10M"),
            Client(name="TEST_003", entity_type="S-Corp", industry="Finance", revenue_range="10-50M"),
            Client(name="TEST_004", entity_type="LLC", industry="Healthcare", revenue_range="1-10M"),
            Client(name="TEST_005", entity_type="C-Corp", industry="Energy", revenue_range="50M+"),
        ]
        stats2 = import_clients(test_db, clients2, skip_existing=True)
        assert stats2["inserted"] == 2  # Only new ones
        assert stats2["skipped"] == 3  # Existing ones

        # Verify total count
        assert test_db.query(Client).count() == 5


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_csv_file(self):
        """Test reading empty CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            csv_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="empty or has no header"):
                read_csv_file(csv_path)
        finally:
            csv_path.unlink()

    def test_csv_with_only_header(self):
        """Test CSV with only header row."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "name", "entity_type", "industry", "revenue_range",
                "industry_naics", "ca_nexus", "tx_nexus", "fl_nexus",
                "tax_credits_used"
            ])
            writer.writeheader()
            csv_path = Path(f.name)

        try:
            clients = read_csv_file(csv_path)
            assert len(clients) == 0
        finally:
            csv_path.unlink()

    def test_malformed_boolean_in_row(self):
        """Test CSV row with malformed boolean value."""
        row = {
            "name": "TEST_001",
            "entity_type": "LLC",
            "industry": "Retail",
            "revenue_range": "<1M",
            "ca_nexus": "YES",  # Invalid boolean
            "tx_nexus": "False",
            "fl_nexus": "False",
            "tax_credits_used": "",
        }

        with pytest.raises(ValueError, match="Invalid boolean value"):
            parse_csv_row(row, row_number=2)
