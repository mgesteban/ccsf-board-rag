"""
URL Discovery Module for CCSF Board Meeting Documents

Scrapes the Granicus archive to find all agenda and minutes URLs.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
from bs4 import BeautifulSoup


GRANICUS_ARCHIVE_URL = "https://ccsf.granicus.com/ViewPublisher.php?view_id=3"
OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "document_urls.json"


def discover_meeting_urls() -> dict:
    """
    Scrape the Granicus archive page to discover all meeting URLs.

    Returns:
        dict: Meeting data in the schema:
            {
                "scraped_at": "ISO timestamp",
                "source_url": "archive URL",
                "total_meetings": int,
                "meetings": [
                    {
                        "meeting_id": "meeting_YYYY_MM_DD",
                        "date": "YYYY-MM-DD",
                        "title": "Meeting title",
                        "agenda_url": "URL or null",
                        "minutes_url": "URL or null"
                    }
                ]
            }
    """
    print(f"Fetching archive page: {GRANICUS_ARCHIVE_URL}")

    response = requests.get(GRANICUS_ARCHIVE_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    meetings = []

    # Find all table rows containing meeting data
    for row in soup.find_all('tr'):
        tds = row.find_all('td')
        if len(tds) < 2:
            continue

        row_text = row.get_text()

        # Extract date (format: "Mon DD, YYYY")
        date_match = re.search(r'([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})', row_text)
        if not date_match:
            continue

        date_str = date_match.group(1)

        # Get title from first column
        title = tds[0].get_text(strip=True)

        # Find agenda and minutes links
        agenda_url = None
        minutes_url = None

        for link in row.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()

            # Make absolute URL if needed
            if not href.startswith('http'):
                href = f"https://ccsf.granicus.com/{href}"

            if link_text == 'agenda' and 'AgendaViewer' in href:
                agenda_url = href
            elif link_text == 'minutes' and 'MinutesViewer' in href:
                minutes_url = href

        if agenda_url or minutes_url:
            # Parse date for meeting_id
            try:
                parsed_date = datetime.strptime(date_str, '%b %d, %Y')
                meeting_id = f"meeting_{parsed_date.strftime('%Y_%m_%d')}"
                iso_date = parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                meeting_id = f"meeting_unknown_{len(meetings)}"
                iso_date = date_str

            meetings.append({
                'meeting_id': meeting_id,
                'date': iso_date,
                'title': title,
                'agenda_url': agenda_url,
                'minutes_url': minutes_url
            })

    # Sort by date descending
    meetings.sort(key=lambda x: x['date'], reverse=True)

    result = {
        'scraped_at': datetime.now().isoformat() + 'Z',
        'source_url': GRANICUS_ARCHIVE_URL,
        'total_meetings': len(meetings),
        'meetings': meetings
    }

    print(f"Found {len(meetings)} meetings")
    if meetings:
        print(f"Date range: {meetings[-1]['date']} to {meetings[0]['date']}")

    return result


def save_urls(data: dict, output_path: Optional[Path] = None) -> Path:
    """Save discovered URLs to JSON file."""
    output_path = output_path or OUTPUT_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Saved to {output_path}")
    return output_path


def load_urls(input_path: Optional[Path] = None) -> dict:
    """Load previously discovered URLs from JSON file."""
    input_path = input_path or OUTPUT_FILE

    with open(input_path, 'r') as f:
        return json.load(f)


def get_stats() -> dict:
    """Get statistics about discovered documents."""
    data = load_urls()

    meetings = data['meetings']
    agendas = sum(1 for m in meetings if m['agenda_url'])
    minutes = sum(1 for m in meetings if m['minutes_url'])

    return {
        'total_meetings': data['total_meetings'],
        'with_agenda': agendas,
        'with_minutes': minutes,
        'date_range': {
            'earliest': meetings[-1]['date'] if meetings else None,
            'latest': meetings[0]['date'] if meetings else None
        },
        'scraped_at': data['scraped_at']
    }


if __name__ == '__main__':
    # When run directly, discover URLs and save
    data = discover_meeting_urls()
    save_urls(data)

    stats = get_stats()
    print(f"\nStatistics:")
    print(f"  Total meetings: {stats['total_meetings']}")
    print(f"  With agenda: {stats['with_agenda']}")
    print(f"  With minutes: {stats['with_minutes']}")
    print(f"  Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
