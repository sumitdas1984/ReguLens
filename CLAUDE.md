# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ReguLens monitors IRS regulatory updates and alerts tax professionals when clients are affected.

**Current Phase**: Data acquisition (scrapers working, normalization next)

## Development Setup

```bash
# Install dependencies
uv sync

# Run scrapers
uv run python scripts/scrape_irs_newsroom.py
uv run python scripts/scrape_irs_irb.py

# Run notebook
uv run jupyter notebook notebooks/
```

## Project Structure

```
ReguLens/
├── scripts/           # Standalone scraper scripts
│   ├── scrape_irs_newsroom.py   # IRS Newsroom scraper
│   └── scrape_irs_irb.py        # IRS IRB scraper
├── notebooks/         # Jupyter notebooks for exploration
├── data/             # Scraped data (JSON state files)
├── docs/            # Project documentation
└── pyproject.toml   # Dependencies
```

## Data Sources

| Source | URL |
|--------|-----|
| IRS Newsroom | https://www.irs.gov/newsroom-index-search |
| IRS IRB | https://www.irs.gov/internal-revenue-bulletins |

## Important Technical Notes

### Cookie Handling
Government sites require session + cookie handling:
```python
with httpx.Client(follow_redirects=True, headers=HEADERS) as client:
    client.get("https://www.irs.gov/")  # Get cookies first
    response = client.get(target_url)
```

### IRS Newsroom Sorting
Default sort is NOT by date. Must use sort parameter:
```
?order=field_pup_release_date&sort=desc
```

### Incremental Scraping
Scrapers use change detection — store previous state in JSON, compare on each run.

## Architecture Philosophy

**Foundation-first**: Solve data acquisition before AI/LLM.

| Most Projects | ReguLens |
|---------------|----------|
| Jump to LLM/Agents | ✅ Build scrapers first |
| Hope sources stay up | ✅ Test reliability |
| Generic handling | ✅ Domain-specific |

## Road to MVP

1. ✅ Scraping Infrastructure (experimental scrapers created)
2. 🔄 Scraping Infrastructure (current - scheduling, error handling)
3. ⏳ Knowledge Engineering & Normalization
4. ⏳ Client Profiles & Matching
5. ⏳ Alerting System

After MVP: Dashboard, cloud deployment

## Adding New Scrapers

1. Create `scripts/scrape_<source>.py`
2. Use `httpx` with session + cookie handling
3. Implement change detection (compare against previous state)
4. Store state in `data/<source>_entries.json`

## Key Dependencies

- `httpx` — HTTP client with cookie handling
- `beautifulsoup4` — HTML parsing
- `jupyter` — Notebooks
- `pandas` — Data analysis
