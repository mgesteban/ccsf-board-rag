#!/usr/bin/env python3
"""
Script 1: Discover Document URLs

Scrapes the CCSF Granicus archive to find all board meeting
agenda and minutes URLs.

Usage:
    python scripts/01_discover_urls.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scraper.url_discovery import discover_meeting_urls, save_urls, get_stats


def main():
    print("=" * 60)
    print("CCSF Board Meeting URL Discovery")
    print("=" * 60)

    # Discover URLs
    data = discover_meeting_urls()

    # Save to file
    save_urls(data)

    # Print statistics
    stats = get_stats()
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"  Total meetings: {stats['total_meetings']}")
    print(f"  With agenda:    {stats['with_agenda']}")
    print(f"  With minutes:   {stats['with_minutes']}")
    print(f"  Date range:     {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
    print(f"\nData saved to: data/document_urls.json")
    print("\nNext step: Run scripts/02_extract_documents.py")


if __name__ == '__main__':
    main()
