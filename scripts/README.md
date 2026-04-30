# ReguLens Utility Scripts

This directory contains standalone utility scripts for ReguLens.

## Future Scripts

- `import_clients.py`: Import client profiles from CSV to database
- `run_scraper.py`: Manually trigger a scraper run
- `test_email.py`: Test email configuration

## Development Guidelines

- Scripts should be standalone (not dependent on FastAPI app running)
- Use argparse for command-line arguments
- Include docstrings and usage examples
- Handle errors gracefully with clear messages
