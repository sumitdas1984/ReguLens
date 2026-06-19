# Data Acquisition Strategy

## Sources

| Source | Content | Frequency |
|--------|---------|-----------|
| [IRS Newsroom](https://www.irs.gov/newsroom-index-search) | News Releases, Tax Tips, Fact Sheets | Daily |
| [IRS IRB](https://www.irs.gov/internal-revenue-bulletins) | Notices, Revenue Rulings | Weekly |

## Incremental Scraping

Track state between runs to only process new entries:

```
Fetch → Diff (by URL) → New Entries → Process → Update State
```

## Scripts

| Script | State File |
|--------|------------|
| `scripts/scrape_irs_newsroom.py` | `data/irs_entries.json` |
| `scripts/scrape_irs_irb.py` | `data/irs_irb_bulletins.json` |

## Technical Notes

- **Cookies**: IRS requires visiting homepage first to get cookies
- **Sort**: Default sort is not by date. Use `?order=field_pup_release_date&sort=desc`
- **PDF**: IRB content is in PDFs (future extraction planned)

## Future

- Scheduling (APScheduler)
- PDF content extraction
- Additional source evaluation
