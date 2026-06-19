#!/usr/bin/env python3
"""
IRS Newsroom Index Scraper

Fetches the IRS Newsroom Index page and extracts entries.
Stores state to detect new entries between runs.

Usage:
    python scripts/scrape_irs_newsroom.py           # Run scraper
    python scripts/scrape_irs_newsroom.py --show   # Show all entries
    python scripts/scrape_irs_newsroom.py --new     # Show only new entries
"""

import argparse
import json
import os
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.irs.gov/newsroom-index-search"
# Sort by date descending (newest first) - same as clicking Date column header
SORT_PARAM = "&order=field_pup_release_date&sort=desc"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
STATE_FILE = "data/irs_entries.json"


def create_client():
    return httpx.Client(follow_redirects=True, headers=HEADERS)


def fetch_page(page=0):
    with create_client() as client:
        client.get("https://www.irs.gov/", headers=HEADERS)
        # Use sort parameter to get entries sorted by date descending (newest first)
        base = f"{BASE_URL}?{SORT_PARAM[1:]}"  # Remove leading & from SORT_PARAM
        if page == 0:
            url = base
        else:
            url = f"{base}&page={page}"
        return client.get(url, headers=HEADERS)


def parse_entry(row):
    cells = row.find_all("td")
    if len(cells) < 3:
        return None
    title_link = cells[0].find("a")
    if not title_link:
        return None
    title = title_link.get_text(strip=True)
    link = title_link.get("href", "")
    if link and not link.startswith("http"):
        link = f"https://www.irs.gov{link}"
    return {
        "title": title,
        "date": cells[1].get_text(strip=True),
        "type": cells[2].get_text(strip=True),
        "link": link,
        "source": "IRS Newsroom",
    }


def scrape(max_pages=5):
    all_entries = []
    for page in range(max_pages):
        response = fetch_page(page)
        if response.status_code != 200:
            print(f"Page {page}: Failed with status {response.status_code}")
            break
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:
            break
        rows = table.find_all("tr")[1:]
        if not rows:
            break
        for row in rows:
            entry = parse_entry(row)
            if entry:
                all_entries.append(entry)
        print(f"Page {page}: Found {len(rows)} entries")

    # Sort by date descending (newest first)
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return datetime.min

    all_entries.sort(key=lambda e: parse_date(e["date"]), reverse=True)
    return all_entries


def load_previous_entries():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return []


def save_entries(entries):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def find_new_entries(current, previous):
    previous_links = {e["link"] for e in previous}
    return [e for e in current if e["link"] not in previous_links]


def main():
    parser = argparse.ArgumentParser(description="IRS Newsroom Scraper")
    parser.add_argument("--show", action="store_true", help="Show all entries")
    parser.add_argument("--new", action="store_true", help="Show only new entries")
    parser.add_argument("--pages", type=int, default=5, help="Max pages to scrape")
    args = parser.parse_args()

    print(f"Scraping IRS Newsroom Index...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 50)

    current_entries = scrape(max_pages=args.pages)
    previous_entries = load_previous_entries()
    new_entries = find_new_entries(current_entries, previous_entries)

    print("-" * 50)
    print(f"Current entries: {len(current_entries)}")
    print(f"Previous entries: {len(previous_entries)}")
    print(f"New entries: {len(new_entries)}")

    if args.show:
        print("\n=== ALL ENTRIES ===")
        for e in current_entries:
            print(f"{e['date']} | {e['type']:15} | {e['title'][:60]}")

    if args.new:
        print("\n=== NEW ENTRIES ===")
        if new_entries:
            for e in new_entries:
                print(f"{e['date']} | {e['type']:15} | {e['title'][:60]}")
        else:
            print("No new entries found.")

    if new_entries and not args.show and not args.new:
        print("\nNew entries found! Use --show or --new to see details.")

    save_entries(current_entries)
    print(f"\nState saved to {STATE_FILE}")


if __name__ == "__main__":
    main()
