"""
Import client profiles from CSV file into PostgreSQL database.

Usage:
    python scripts/import_clients.py data/sample/client_profiles_mvp.csv
    python scripts/import_clients.py data/sample/client_profiles_mvp.csv --dry-run
    python scripts/import_clients.py data/sample/client_profiles_mvp.csv --force

This script is idempotent - running multiple times will not create duplicates.
"""

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import Client


def parse_boolean(value: str) -> bool:
    """
    Convert string boolean to Python bool.

    Args:
        value: String value ('True', 'False', or empty)

    Returns:
        Boolean value

    Raises:
        ValueError: If value is not a valid boolean string
    """
    if value == "" or value is None:
        return False
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"Invalid boolean value: '{value}'. Expected 'True', 'False', or empty string.")


def parse_tax_credits(value: str) -> List[str]:
    """
    Parse pipe-delimited tax credits into list.

    Args:
        value: Pipe-delimited string (e.g., "R&D|Other")

    Returns:
        List of tax credit strings
    """
    if not value or value.strip() == "":
        return []

    return [credit.strip() for credit in value.split("|") if credit.strip()]


def parse_csv_row(row: Dict[str, str], row_number: int) -> Client:
    """
    Parse a CSV row into a Client model instance.

    Args:
        row: Dictionary of column name to value
        row_number: Row number for error reporting

    Returns:
        Client instance

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    required_fields = ["name", "entity_type", "industry", "revenue_range"]
    missing_fields = [field for field in required_fields if not row.get(field, "").strip()]

    if missing_fields:
        raise ValueError(
            f"Row {row_number}: Missing required fields: {', '.join(missing_fields)}"
        )

    try:
        # Parse optional industry_naics (empty string -> None)
        industry_naics = row.get("industry_naics", "").strip()
        industry_naics = industry_naics if industry_naics else None

        # Create Client instance (do NOT use id, created_at, updated_at from CSV)
        client = Client(
            name=row["name"].strip(),
            entity_type=row["entity_type"].strip(),
            industry=row["industry"].strip(),
            industry_naics=industry_naics,
            ca_nexus=parse_boolean(row.get("ca_nexus", "")),
            tx_nexus=parse_boolean(row.get("tx_nexus", "")),
            fl_nexus=parse_boolean(row.get("fl_nexus", "")),
            revenue_range=row["revenue_range"].strip(),
            tax_credits_used=parse_tax_credits(row.get("tax_credits_used", "")),
        )

        return client

    except ValueError as e:
        raise ValueError(f"Row {row_number}: {str(e)}")


def read_csv_file(csv_path: Path) -> List[Client]:
    """
    Read and parse CSV file into list of Client instances.

    Args:
        csv_path: Path to CSV file

    Returns:
        List of successfully parsed Client instances

    Raises:
        FileNotFoundError: If CSV file does not exist
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    print(f"Reading CSV file: {csv_path}")

    clients = []
    failed_rows = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate expected columns are present
        expected_columns = {
            "name", "entity_type", "industry", "revenue_range",
            "ca_nexus", "tx_nexus", "fl_nexus", "tax_credits_used"
        }

        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row")

        missing_columns = expected_columns - set(reader.fieldnames)
        if missing_columns:
            raise ValueError(
                f"CSV missing required columns: {', '.join(missing_columns)}"
            )

        # Parse each row
        for row_number, row in enumerate(reader, start=2):  # Start at 2 (after header)
            try:
                client = parse_csv_row(row, row_number)
                clients.append(client)
            except ValueError as e:
                print(f"WARNING: {e}")
                failed_rows.append(row_number)

    print(f"Successfully parsed {len(clients)} clients")
    if failed_rows:
        print(f"Failed to parse {len(failed_rows)} rows: {failed_rows}")

    return clients


def check_existing_clients(db: Session, client_names: List[str]) -> Dict[str, bool]:
    """
    Check which client names already exist in database.

    Args:
        db: Database session
        client_names: List of client names to check

    Returns:
        Dictionary mapping client name to existence (True if exists)
    """
    if not client_names:
        return {}

    existing = db.query(Client.name).filter(Client.name.in_(client_names)).all()
    existing_names = {name for (name,) in existing}

    return {name: (name in existing_names) for name in client_names}


def import_clients(
    db: Session,
    clients: List[Client],
    skip_existing: bool = True,
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Import clients into database with batch processing.

    Args:
        db: Database session
        clients: List of Client instances to import
        skip_existing: If True, skip clients that already exist
        batch_size: Number of clients to insert per batch

    Returns:
        Dictionary with statistics (total, inserted, skipped, failed)
    """
    stats = {
        "total": len(clients),
        "inserted": 0,
        "skipped": 0,
        "failed": 0,
    }

    if not clients:
        return stats

    # Check for existing clients
    client_names = [client.name for client in clients]
    existing_map = check_existing_clients(db, client_names)

    # Filter out existing clients if skip_existing is True
    if skip_existing:
        clients_to_insert = [
            client for client in clients
            if not existing_map.get(client.name, False)
        ]
        stats["skipped"] = len(clients) - len(clients_to_insert)

        if stats["skipped"] > 0:
            print(f"Skipping {stats['skipped']} existing clients")
    else:
        clients_to_insert = clients

    if not clients_to_insert:
        return stats

    # Process in batches
    total_batches = (len(clients_to_insert) + batch_size - 1) // batch_size
    print(f"\nImporting {len(clients_to_insert)} clients in batches of {batch_size}...")

    for i in range(0, len(clients_to_insert), batch_size):
        batch = clients_to_insert[i:i + batch_size]
        batch_number = (i // batch_size) + 1

        try:
            db.bulk_save_objects(batch)
            db.commit()
            stats["inserted"] += len(batch)
            print(f"  Batch {batch_number}/{total_batches}: Inserted {len(batch)} clients")

        except (SQLAlchemyError, IntegrityError) as e:
            db.rollback()
            stats["failed"] += len(batch)
            print(f"  ERROR: Batch {batch_number} failed: {e}")

    return stats


def delete_all_clients(db: Session) -> int:
    """
    Delete all clients from database (for --force flag).

    Args:
        db: Database session

    Returns:
        Number of clients deleted
    """
    count = db.query(Client).count()
    db.query(Client).delete(synchronize_session='fetch')
    db.commit()
    return count


def print_summary(stats: Dict[str, Any], elapsed_time: float) -> int:
    """
    Print import summary and return exit code.

    Args:
        stats: Statistics dictionary
        elapsed_time: Time taken in seconds

    Returns:
        Exit code (0 if no failures, 1 if any failures)
    """
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Total clients in CSV:  {stats['total']}")
    print(f"Successfully inserted: {stats['inserted']}")
    print(f"Skipped (existing):    {stats['skipped']}")
    print(f"Failed:                {stats['failed']}")
    print(f"Elapsed time:          {elapsed_time:.2f} seconds")
    print("=" * 60)

    if stats['failed'] > 0:
        print("\nImport completed with errors!")
        return 1
    else:
        print("\nImport completed successfully!")
        return 0


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Import client profiles from CSV into PostgreSQL database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/import_clients.py data/sample/client_profiles_mvp.csv
  python scripts/import_clients.py data/sample/client_profiles_mvp.csv --dry-run
  python scripts/import_clients.py data/sample/client_profiles_mvp.csv --force
        """
    )

    parser.add_argument(
        "csv_file",
        type=str,
        help="Path to CSV file containing client profiles"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV without importing to database"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete all existing clients before importing (requires confirmation)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of clients to insert per batch (default: 50)"
    )

    return parser.parse_args()


def main() -> int:
    """
    Main function - orchestrates the import process.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    start_time = time.time()

    try:
        # Parse arguments
        args = parse_arguments()
        csv_path = Path(args.csv_file)

        # Validate batch_size
        if args.batch_size < 1:
            print("ERROR: --batch-size must be at least 1")
            return 1

        # Read and parse CSV
        clients = read_csv_file(csv_path)

        if not clients:
            print("ERROR: No valid clients found in CSV file")
            return 1

        # Handle dry-run mode
        if args.dry_run:
            print(f"\n[DRY RUN] Would import {len(clients)} clients")
            print("No changes made to database.")
            return 0

        # Connect to database
        print("\nConnecting to database...")
        db = SessionLocal()

        try:
            # Test connection
            db.execute(text("SELECT 1"))
            print("Database connection successful")

            # Handle force mode
            if args.force:
                print("\n" + "!" * 60)
                print("WARNING: --force will DELETE ALL existing clients")
                print("!" * 60)
                response = input("Continue? Type 'yes' to confirm: ")

                if response.strip().lower() == "yes":
                    deleted_count = delete_all_clients(db)
                    print(f"Deleted {deleted_count} existing clients")
                else:
                    print("Import cancelled by user")
                    return 0

            # Import clients (always skip existing - use --force to reimport all)
            stats = import_clients(
                db,
                clients,
                skip_existing=True,
                batch_size=args.batch_size
            )

            elapsed_time = time.time() - start_time
            return print_summary(stats, elapsed_time)

        finally:
            db.close()

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    except SQLAlchemyError as e:
        print(f"ERROR: Database connection failed: {e}")
        return 1

    except KeyboardInterrupt:
        print("\n\nImport interrupted by user")
        return 1

    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
