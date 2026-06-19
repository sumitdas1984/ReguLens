#!/usr/bin/env python3
"""
IRS Internal Revenue Bulletin (IRB) Scraper

Fetches the IRB page and extracts bulletin listings.
Bulletins are published weekly as PDFs.

Source: https://www.irs.gov/internal-revenue-bulletins

Note: Individual notices/rulings are inside PDFs.
This scraper extracts the bulletin list. PDF content extraction
would require additional libraries (PyPDF2, pdfplumber, etc.)

Usage:
    python scripts/scrape_irs_irb.py           # Run scraper
    python scripts/scrape_irs_irb.py --show   # Show all bulletins
    python scripts/scrape_irs_irb.py --new    # Show only new bulletins
"""

import argparse
import json
import os
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.irs.gov/internal-revenue-bulletins"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
STATE_FILE = "data/irs_irb_bulletins.json"


def fetch_page():
    with httpx.Client(follow_redirects=True, headers=HEADERS) as client:
        client.get("https://www.irs.gov/", headers=HEADERS)
        return client.get(BASE_URL, headers=HEADERS)


def parse_bulletins(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    bulletins = []
    for row in table.find_all("tr")[1:]:  # Skip header
        cells = row.find_all("td")
        if len(cells) >= 2:
            link = cells[0].find("a")
            if link:
                title = link.get_text(strip=True)
                href = link.get("href", "")

                # Handle relative URLs
                if href.startswith("/"):
                    pdf_url = f"https://www.irs.gov{href}"
                elif href.startswith("http"):
                    pdf_url = href
                else:
                    pdf_url = f"https://www.irs.gov/pub/{href}"

                # Extract bulletin year and number from title
                # e.g., "Internal Revenue Bulletin 2026-26"
                parts = title.replace("Internal Revenue Bulletin", "").strip().split("-")
                year = parts[0] if len(parts) > 0 else ""
                number = parts[1] if len(parts) > 1 else ""

                bulletins.append({
                    "title": title,
                    "year": year,
                    "number": number,
                    "published": cells[1].get_text(strip=True),
                    "pdf_url": pdf_url,
                    "source": "IRS IRB",
                })

    return bulletins


def load_previous():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return []


def save_bulletins(bulletins):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(bulletins, f, indent=2)


def find_new_bulletins(current, previous):
    previous_urls = {b["pdf_url"] for b in previous}
    return [b for b in current if b["pdf_url"] not in previous_urls]


def main():
    parser = argparse.ArgumentParser(description="IRS IRB Scraper")
    parser.add_argument("--show", action="store_true", help="Show all bulletins")
    parser.add_argument("--new", action="store_true", help="Show only new bulletins")
    args = parser.parse_args()

    print("Scraping IRS Internal Revenue Bulletins...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 50)

    response = fetch_page()
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print("Failed to fetch page!")
        return

    current_bulletins = parse_bulletins(response.text)
    previous_bulletins = load_previous()
    new_bulletins = find_new_bulletins(current_bulletins, previous_bulletins)

    print("-" * 50)
    print(f"Current bulletins: {len(current_bulletins)}")
    print(f"Previous bulletins: {len(previous_bulletins)}")
    print(f"New bulletins: {len(new_bulletins)}")

    if args.show:
        print("\n=== ALL BULLETINS ===")
        for b in current_bulletins:
            print(f"{b['published']} | {b['year']}-{b['number']} | {b['title'][:40]}")

    if args.new:
        print("\n=== NEW BULLETINS ===")
        if new_bulletins:
            for b in new_bulletins:
                print(f"{b['published']} | {b['year']}-{b['number']} | {b['title'][:40]}")
                print(f"  PDF: {b['pdf_url']}")
        else:
            print("No new bulletins found.")

    if new_bulletins and not args.show and not args.new:
        print("\nNew bulletins found! Use --show or --new to see details.")

    save_bulletins(current_bulletins)
    print(f"\nState saved to {STATE_FILE}")


if __name__ == "__main__":
    main()
