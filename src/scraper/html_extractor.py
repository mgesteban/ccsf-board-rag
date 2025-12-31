"""
HTML Extractor Module for CCSF Board Meeting Agendas

Extracts text content from Granicus agenda HTML pages.
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup


OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed"


def extract_agenda_text(agenda_url: str, timeout: int = 30) -> dict:
    """
    Extract text content from a Granicus agenda page.

    Args:
        agenda_url: URL to the AgendaViewer.php page
        timeout: Request timeout in seconds

    Returns:
        dict: Extracted content with metadata:
            {
                "source_url": str,
                "document_type": "agenda",
                "content": str,
                "sections": list,
                "extraction_timestamp": str,
                "metadata": dict
            }
    """
    print(f"Extracting agenda from: {agenda_url}")

    # Parse clip_id from URL for identification
    parsed = urlparse(agenda_url)
    params = parse_qs(parsed.query)
    clip_id = params.get('clip_id', ['unknown'])[0]

    response = requests.get(agenda_url, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract meeting header info
    header_info = _extract_header(soup)

    # Extract all agenda sections
    sections = _extract_sections(soup)

    # Combine into full text content
    content_parts = []

    # Add header
    if header_info:
        content_parts.append(header_info)
        content_parts.append("\n" + "=" * 60 + "\n")

    # Add each section
    for section in sections:
        content_parts.append(f"\n{section['number']}. {section['title']}")
        if section['items']:
            for item in section['items']:
                content_parts.append(f"   {item['letter']}. {item['text']}")

    full_content = "\n".join(content_parts)

    return {
        "source_url": agenda_url,
        "document_type": "agenda",
        "clip_id": clip_id,
        "content": full_content,
        "header": header_info,
        "sections": sections,
        "extraction_timestamp": datetime.now().isoformat() + "Z",
        "metadata": {
            "character_count": len(full_content),
            "section_count": len(sections)
        }
    }


def _extract_header(soup: BeautifulSoup) -> str:
    """Extract the meeting header information."""
    # The header is typically in the first table with strong tags
    first_table = soup.find('table')
    if first_table:
        strong_tags = first_table.find_all('strong')
        if strong_tags:
            header_texts = []
            for strong in strong_tags:
                text = strong.get_text(separator=' ', strip=True)
                if text:
                    header_texts.append(text)
            return "\n".join(header_texts)
    return ""


def _extract_sections(soup: BeautifulSoup) -> list:
    """Extract all agenda sections with their items."""
    sections = []

    # Find all tables that contain agenda items
    # Agenda items are in tables with cells containing numbers like "1.", "2.", etc.
    all_tables = soup.find_all('table')

    current_section = None

    for table in all_tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                first_cell = cells[0].get_text(strip=True)
                second_cell = cells[1].get_text(strip=True)

                # Check if this is a main section (numbered like "1.", "2.")
                if re.match(r'^\d+\.$', first_cell):
                    section_num = first_cell.rstrip('.')
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        'number': section_num,
                        'title': second_cell,
                        'items': []
                    }

                # Check if this is a sub-item (lettered like "A.", "B.")
                elif re.match(r'^[A-Z]\.$', first_cell) and current_section:
                    current_section['items'].append({
                        'letter': first_cell.rstrip('.'),
                        'text': second_cell
                    })

    # Don't forget the last section
    if current_section:
        sections.append(current_section)

    return sections


def save_extracted_agenda(data: dict, output_dir: Optional[Path] = None) -> Path:
    """Save extracted agenda to JSON file."""
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create filename from clip_id
    clip_id = data.get('clip_id', 'unknown')
    filename = f"agenda_{clip_id}.json"
    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved agenda to {output_path}")
    return output_path


def extract_and_save_agenda(agenda_url: str, output_dir: Optional[Path] = None) -> dict:
    """
    Extract agenda and save to file.

    Args:
        agenda_url: URL to the agenda page
        output_dir: Optional output directory

    Returns:
        dict: Extracted data
    """
    data = extract_agenda_text(agenda_url)
    save_extracted_agenda(data, output_dir)
    return data


if __name__ == '__main__':
    # Test with a sample agenda
    test_url = "https://ccsf.granicus.com/AgendaViewer.php?view_id=3&clip_id=2291"
    result = extract_and_save_agenda(test_url)
    print(f"\nExtracted {result['metadata']['section_count']} sections")
    print(f"Total characters: {result['metadata']['character_count']}")
    print(f"\nFirst 500 chars of content:")
    print(result['content'][:500])
