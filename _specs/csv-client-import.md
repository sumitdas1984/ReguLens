# Spec for CSV Client Import Script

branch: claude/feature/csv-client-import

## Summary
Create a Python script to import 100 sample client profiles from CSV file into the PostgreSQL database. This provides the initial client data needed for testing scrapers and AI matching functionality in the MVP.

**Note**: The CSV file `data/sample/client_profiles_mvp.csv` already exists with 100 sample client profiles. This spec covers the import script to load that data into the database.

## Functional Requirements

### Script Functionality
- Create `scripts/import_clients.py` to import client data from CSV
- Read from `data/sample/client_profiles_mvp.csv` (100 client profiles)
- Parse CSV rows and map to Client model fields
- Insert clients into PostgreSQL database using SQLAlchemy
- Handle duplicate entries gracefully (skip or update based on client name)
- Validate required fields before insertion
- Log import progress (clients processed, succeeded, failed)
- Provide clear success/failure summary at completion

### CSV to Model Mapping
Map CSV columns to Client model fields:
- `name` → Client.name (client code like TECH_001)
- `entity_type` → Client.entity_type (C-Corp, S-Corp, LLC, etc.)
- `industry` → Client.industry
- `industry_naics` → Client.industry_naics (optional)
- `ca_nexus` → Client.ca_nexus (boolean: Y/N or True/False)
- `tx_nexus` → Client.tx_nexus (boolean)
- `fl_nexus` → Client.fl_nexus (boolean)
- `revenue_range` → Client.revenue_range (<1M, 1-10M, 10-50M, 50M+)
- `tax_credits_used` → Client.tax_credits_used (array: comma-separated or JSON)

### Script Behavior
- **Idempotent**: Can be run multiple times without creating duplicates
- **Clear output**: Show progress during import (e.g., "Importing client 1/100...")
- **Summary report**: Display total processed, succeeded, failed, skipped
- **Error handling**: Continue processing even if individual rows fail
- **Database connection**: Use existing database configuration from settings
- **Transaction safety**: Use database transactions to ensure consistency

## Possible Edge Cases

### Data Quality
- Empty or missing required fields in CSV
- Invalid boolean values for nexus flags (not Y/N or True/False)
- Invalid entity types not matching expected values
- Malformed tax_credits_used (not parseable as array)
- CSV encoding issues (UTF-8 vs other encodings)
- Trailing/leading whitespace in fields

### Database State
- Database connection failure
- Client with same name already exists (duplicate detection)
- Database constraint violations (e.g., foreign key errors)
- Transaction rollback scenarios
- Empty database vs pre-populated database

### Script Execution
- CSV file not found or not readable
- Insufficient database permissions
- Script run with wrong working directory
- Script interrupted mid-import (partial import state)
- Running script multiple times consecutively

## Acceptance Criteria

### Script Creation
- [ ] `scripts/import_clients.py` created and executable
- [ ] Script uses SQLAlchemy session from database configuration
- [ ] Script reads from `data/sample/client_profiles_mvp.csv`
- [ ] All Client model fields are mapped from CSV columns

### Import Functionality
- [ ] Successfully imports all 100 client profiles
- [ ] CSV parsing handles all field types correctly (strings, booleans, arrays)
- [ ] Boolean conversion works (Y/N or True/False → boolean)
- [ ] Array conversion works (comma-separated or JSON → list)
- [ ] Required fields are validated before insertion

### Error Handling
- [ ] Duplicate client names are detected and handled (skip or log warning)
- [ ] Invalid data rows are logged but don't stop the import
- [ ] Database connection errors are caught and reported
- [ ] CSV file not found error is handled gracefully

### Idempotency
- [ ] Running script twice doesn't create 200 clients
- [ ] Existing clients are either skipped or updated (configurable)
- [ ] Script can recover from partial import state

### Output and Logging
- [ ] Progress shown during import (e.g., "Processing client 25/100")
- [ ] Success/failure logged for each client
- [ ] Final summary shows: total processed, succeeded, failed, skipped
- [ ] Clear error messages for failures

### Verification
- [ ] After running script, database contains 100 clients
- [ ] All client fields are populated correctly
- [ ] Can query clients by state nexus (CA, TX, FL)
- [ ] Can verify client data matches CSV source

## Open Questions

- Should duplicate handling skip or update existing clients?
- Should the script support command-line arguments (e.g., --file path, --force)?
- Should there be a dry-run mode to preview without importing?
- Should the script support other CSV files or just the MVP sample?
- Should there be a rollback option if import fails midway?

## Testing Guidelines

Create test file(s) in the ./tests folder for the import script, and create meaningful tests for the following cases, without going too heavy:

### Unit Tests
- Test CSV parsing logic with sample data
- Test field mapping and type conversion (booleans, arrays)
- Test duplicate detection logic
- Test validation of required fields
- Test error handling for invalid data

### Integration Tests
- Test full import with small test CSV file (5-10 clients)
- Test idempotency (run import twice, verify no duplicates)
- Test import with existing clients in database
- Test error handling with malformed CSV
- Test database rollback on critical errors

### Manual Verification
- Run script with actual `client_profiles_mvp.csv`
- Verify 100 clients imported successfully
- Query database to check client data correctness
- Test re-running script (no duplicates created)
- Verify state nexus flags work for filtering
