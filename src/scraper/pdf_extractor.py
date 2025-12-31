"""
PDF Extractor Module for CCSF Board Meeting Minutes

Downloads and extracts text from Granicus minutes PDFs.
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs, unquote

import fitz  # PyMuPDF
import requests


RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed"


def get_pdf_url_from_minutes_viewer(minutes_url: str, timeout: int = 30) -> str:
    """
    Get the actual PDF URL from a MinutesViewer.php URL.

    The MinutesViewer redirects to a Google Docs viewer which embeds the PDF.
    We extract the actual PDF URL from the Google viewer URL.

    Args:
        minutes_url: URL to MinutesViewer.php
        timeout: Request timeout

    Returns:
        str: Direct URL to the PDF file
    """
    response = requests.get(minutes_url, allow_redirects=True, timeout=timeout)

    # The final URL should be a Google Docs viewer URL like:
    # https://docs.google.com/gview?url=https%3A%2F%2Fccsf.granicus.com%2FDocumentViewer.php%3Ffile%3D...
    final_url = response.url

    if 'docs.google.com/gview' in final_url:
        parsed = urlparse(final_url)
        params = parse_qs(parsed.query)
        pdf_url = unquote(params.get('url', [''])[0])
        return pdf_url

    # If it's already a direct PDF URL
    if '.pdf' in final_url.lower() or 'DocumentViewer' in final_url:
        return final_url

    raise ValueError(f"Could not extract PDF URL from: {minutes_url}")


def download_pdf(pdf_url: str, output_path: Path, timeout: int = 60) -> Path:
    """
    Download a PDF file.

    Args:
        pdf_url: URL to the PDF
        output_path: Path to save the PDF
        timeout: Request timeout

    Returns:
        Path: Path to the downloaded file
    """
    response = requests.get(pdf_url, timeout=timeout)
    response.raise_for_status()

    # Verify it's actually a PDF
    content_type = response.headers.get('Content-Type', '')
    if 'pdf' not in content_type.lower() and not response.content[:4] == b'%PDF':
        raise ValueError(f"Response is not a PDF: {content_type}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(response.content)

    return output_path


def extract_text_from_pdf(pdf_path: Path) -> dict:
    """
    Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        dict: Extracted content with metadata
    """
    doc = fitz.open(pdf_path)

    pages_text = []
    full_text_parts = []

    for page_num, page in enumerate(doc):
        text = page.get_text()
        pages_text.append({
            'page': page_num + 1,
            'text': text
        })
        full_text_parts.append(text)

    full_text = "\n\n".join(full_text_parts)

    result = {
        "page_count": len(doc),
        "pages": pages_text,
        "content": full_text,
        "metadata": {
            "character_count": len(full_text),
            "word_count": len(full_text.split())
        }
    }

    doc.close()
    return result


def extract_minutes(minutes_url: str, clip_id: str = None,
                    raw_dir: Optional[Path] = None,
                    timeout: int = 60) -> dict:
    """
    Download and extract text from a minutes PDF.

    Args:
        minutes_url: URL to MinutesViewer.php
        clip_id: Optional clip ID for naming
        raw_dir: Directory to save raw PDFs
        timeout: Request timeout

    Returns:
        dict: Extracted content with metadata
    """
    raw_dir = raw_dir or RAW_DIR

    # Parse clip_id from URL if not provided
    if not clip_id:
        parsed = urlparse(minutes_url)
        params = parse_qs(parsed.query)
        clip_id = params.get('clip_id', ['unknown'])[0]

    print(f"Extracting minutes from: {minutes_url}")

    # Get the actual PDF URL
    pdf_url = get_pdf_url_from_minutes_viewer(minutes_url, timeout)
    print(f"  PDF URL: {pdf_url[:80]}...")

    # Download the PDF
    pdf_path = raw_dir / f"minutes_{clip_id}.pdf"
    download_pdf(pdf_url, pdf_path, timeout)
    print(f"  Downloaded to: {pdf_path}")

    # Extract text
    extracted = extract_text_from_pdf(pdf_path)

    return {
        "source_url": minutes_url,
        "pdf_url": pdf_url,
        "document_type": "minutes",
        "clip_id": clip_id,
        "content": extracted["content"],
        "page_count": extracted["page_count"],
        "extraction_timestamp": datetime.now().isoformat() + "Z",
        "metadata": {
            "character_count": extracted["metadata"]["character_count"],
            "word_count": extracted["metadata"]["word_count"],
            "local_file_path": str(pdf_path)
        }
    }


def save_extracted_minutes(data: dict, output_dir: Optional[Path] = None) -> Path:
    """Save extracted minutes to JSON file."""
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    clip_id = data.get('clip_id', 'unknown')
    filename = f"minutes_{clip_id}.json"
    output_path = output_dir / filename

    # Don't save the full content in the JSON to keep file sizes reasonable
    # Just save metadata and reference to the content
    save_data = {
        "source_url": data["source_url"],
        "pdf_url": data["pdf_url"],
        "document_type": data["document_type"],
        "clip_id": data["clip_id"],
        "content": data["content"],
        "page_count": data["page_count"],
        "extraction_timestamp": data["extraction_timestamp"],
        "metadata": data["metadata"]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"Saved minutes to {output_path}")
    return output_path


def extract_and_save_minutes(minutes_url: str, clip_id: str = None,
                             output_dir: Optional[Path] = None) -> dict:
    """
    Extract minutes and save to file.

    Args:
        minutes_url: URL to the minutes page
        clip_id: Optional clip ID
        output_dir: Optional output directory

    Returns:
        dict: Extracted data
    """
    data = extract_minutes(minutes_url, clip_id)
    save_extracted_minutes(data, output_dir)
    return data


if __name__ == '__main__':
    # Test with a sample minutes
    test_url = "https://ccsf.granicus.com/MinutesViewer.php?view_id=3&clip_id=2291&doc_id=7027f933-d9fb-11f0-bb28-005056a89546"
    result = extract_and_save_minutes(test_url)
    print(f"\nExtracted {result['page_count']} pages")
    print(f"Total characters: {result['metadata']['character_count']}")
    print(f"Total words: {result['metadata']['word_count']}")
    print(f"\nFirst 500 chars of content:")
    print(result['content'][:500])
