#!/usr/bin/env python3
"""
Script 2: Extract Documents

Downloads and extracts text from all discovered agendas and minutes.

Usage:
    python scripts/02_extract_documents.py [--limit N] [--skip-existing]
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scraper.url_discovery import load_urls
from scraper.html_extractor import extract_and_save_agenda
from scraper.pdf_extractor import extract_and_save_minutes


DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Delay between requests to be polite to the server
REQUEST_DELAY = 1.0  # seconds


def file_exists(doc_type: str, clip_id: str) -> bool:
    """Check if a document has already been extracted."""
    filename = f"{doc_type}_{clip_id}.json"
    return (PROCESSED_DIR / filename).exists()


def extract_all_documents(limit: int = None, skip_existing: bool = True):
    """
    Extract all documents from the discovered URLs.

    Args:
        limit: Optional limit on number of documents to process
        skip_existing: Skip documents that have already been extracted
    """
    # Load discovered URLs
    data = load_urls()
    meetings = data['meetings']

    print("=" * 60)
    print("CCSF Board Document Extraction")
    print("=" * 60)
    print(f"Total meetings: {len(meetings)}")

    if limit:
        meetings = meetings[:limit]
        print(f"Processing first {limit} meetings")

    # Counters
    agenda_count = 0
    minutes_count = 0
    agenda_errors = []
    minutes_errors = []
    skipped = 0

    # Process each meeting
    for i, meeting in enumerate(meetings):
        meeting_id = meeting.get('meeting_id', f"meeting_{i}")
        date = meeting.get('date', 'unknown')
        agenda_url = meeting.get('agenda_url')
        minutes_url = meeting.get('minutes_url')

        print(f"\n[{i+1}/{len(meetings)}] {date} - {meeting_id}")

        # Extract clip_id from URL
        clip_id = None
        if agenda_url and 'clip_id=' in agenda_url:
            clip_id = agenda_url.split('clip_id=')[1].split('&')[0]
        elif minutes_url and 'clip_id=' in minutes_url:
            clip_id = minutes_url.split('clip_id=')[1].split('&')[0]

        # Extract agenda
        if agenda_url:
            if skip_existing and clip_id and file_exists('agenda', clip_id):
                print(f"  Agenda: Skipped (already exists)")
                skipped += 1
            else:
                try:
                    result = extract_and_save_agenda(agenda_url)
                    agenda_count += 1
                    print(f"  Agenda: {result['metadata']['section_count']} sections")
                    time.sleep(REQUEST_DELAY)
                except Exception as e:
                    print(f"  Agenda: ERROR - {e}")
                    agenda_errors.append({'meeting_id': meeting_id, 'url': agenda_url, 'error': str(e)})

        # Extract minutes
        if minutes_url:
            if skip_existing and clip_id and file_exists('minutes', clip_id):
                print(f"  Minutes: Skipped (already exists)")
                skipped += 1
            else:
                try:
                    result = extract_and_save_minutes(minutes_url, clip_id)
                    minutes_count += 1
                    print(f"  Minutes: {result['page_count']} pages, {result['metadata']['word_count']} words")
                    time.sleep(REQUEST_DELAY)
                except Exception as e:
                    print(f"  Minutes: ERROR - {e}")
                    minutes_errors.append({'meeting_id': meeting_id, 'url': minutes_url, 'error': str(e)})

    # Summary
    print("\n" + "=" * 60)
    print("Extraction Complete")
    print("=" * 60)
    print(f"Agendas extracted:  {agenda_count}")
    print(f"Minutes extracted:  {minutes_count}")
    print(f"Skipped (existing): {skipped}")
    print(f"Agenda errors:      {len(agenda_errors)}")
    print(f"Minutes errors:     {len(minutes_errors)}")

    # Save error log if there were errors
    if agenda_errors or minutes_errors:
        error_log = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'agenda_errors': agenda_errors,
            'minutes_errors': minutes_errors
        }
        error_path = DATA_DIR / 'extraction_errors.json'
        with open(error_path, 'w') as f:
            json.dump(error_log, f, indent=2)
        print(f"\nError log saved to: {error_path}")

    print(f"\nProcessed documents saved to: {PROCESSED_DIR}")
    print("\nNext step: Run scripts/03_build_vectorstore.py")


def main():
    parser = argparse.ArgumentParser(
        description='Extract text from CCSF board meeting documents'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit number of meetings to process'
    )
    parser.add_argument(
        '--skip-existing', '-s',
        action='store_true',
        default=True,
        help='Skip documents that have already been extracted (default: True)'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Re-extract all documents even if they exist'
    )

    args = parser.parse_args()

    skip_existing = not args.force

    extract_all_documents(limit=args.limit, skip_existing=skip_existing)


if __name__ == '__main__':
    main()
