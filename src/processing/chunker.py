"""
Text Chunking Module for CCSF Board Meeting Documents

Splits extracted documents into smaller chunks suitable for RAG retrieval.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional


PROCESSED_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
CHUNKS_DIR = Path(__file__).parent.parent.parent / "data" / "chunks"

# Chunking configuration
TARGET_CHUNK_SIZE = 500  # Target tokens (roughly 4 chars per token)
CHUNK_OVERLAP = 50  # Overlap in tokens
MAX_CHUNK_SIZE = 800  # Maximum chunk size
MIN_CHUNK_SIZE = 100  # Minimum chunk size


def estimate_tokens(text: str) -> int:
    """Estimate token count (roughly 4 characters per token)."""
    return len(text) // 4


def chunk_by_sections(content: str, sections: list, metadata: dict) -> List[dict]:
    """
    Chunk document by its natural section structure.

    For agendas, this means chunking by agenda items.
    Each section becomes one or more chunks depending on size.
    """
    chunks = []
    chunk_index = 0

    # Add header as first chunk if present
    header = metadata.get('header', '')
    if header and estimate_tokens(header) >= MIN_CHUNK_SIZE:
        chunks.append({
            'chunk_index': chunk_index,
            'content': header,
            'token_estimate': estimate_tokens(header),
            'section': 'header',
            'metadata': metadata
        })
        chunk_index += 1

    # Process each section
    for section in sections:
        section_num = section.get('number', '')
        section_title = section.get('title', '')
        items = section.get('items', [])

        # Build section text
        section_text_parts = [f"{section_num}. {section_title}"]

        for item in items:
            letter = item.get('letter', '')
            text = item.get('text', '')
            section_text_parts.append(f"   {letter}. {text}")

        section_text = "\n".join(section_text_parts)
        section_tokens = estimate_tokens(section_text)

        # If section is small enough, keep as one chunk
        if section_tokens <= MAX_CHUNK_SIZE:
            if section_tokens >= MIN_CHUNK_SIZE:
                chunks.append({
                    'chunk_index': chunk_index,
                    'content': section_text,
                    'token_estimate': section_tokens,
                    'section': f"{section_num}. {section_title}",
                    'metadata': metadata
                })
                chunk_index += 1
        else:
            # Split large sections by items
            current_chunk_parts = [f"{section_num}. {section_title}"]
            current_tokens = estimate_tokens(current_chunk_parts[0])

            for item in items:
                letter = item.get('letter', '')
                text = item.get('text', '')
                item_text = f"   {letter}. {text}"
                item_tokens = estimate_tokens(item_text)

                # If adding this item would exceed max, save current and start new
                if current_tokens + item_tokens > MAX_CHUNK_SIZE and current_tokens >= MIN_CHUNK_SIZE:
                    chunk_content = "\n".join(current_chunk_parts)
                    chunks.append({
                        'chunk_index': chunk_index,
                        'content': chunk_content,
                        'token_estimate': current_tokens,
                        'section': f"{section_num}. {section_title}",
                        'metadata': metadata
                    })
                    chunk_index += 1
                    # Start new chunk with section header for context
                    current_chunk_parts = [f"{section_num}. {section_title} (continued)"]
                    current_tokens = estimate_tokens(current_chunk_parts[0])

                current_chunk_parts.append(item_text)
                current_tokens += item_tokens

            # Don't forget the last chunk
            if current_tokens >= MIN_CHUNK_SIZE:
                chunk_content = "\n".join(current_chunk_parts)
                chunks.append({
                    'chunk_index': chunk_index,
                    'content': chunk_content,
                    'token_estimate': current_tokens,
                    'section': f"{section_num}. {section_title}",
                    'metadata': metadata
                })
                chunk_index += 1

    return chunks


def chunk_by_paragraphs(content: str, metadata: dict) -> List[dict]:
    """
    Chunk document by paragraphs with overlap.

    Used for minutes PDFs which don't have structured sections.
    """
    chunks = []

    # Split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    current_chunk_parts = []
    current_tokens = 0
    chunk_index = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If this single paragraph is too large, split it further
        if para_tokens > MAX_CHUNK_SIZE:
            # Save current chunk first
            if current_tokens >= MIN_CHUNK_SIZE:
                chunk_content = "\n\n".join(current_chunk_parts)
                chunks.append({
                    'chunk_index': chunk_index,
                    'content': chunk_content,
                    'token_estimate': current_tokens,
                    'section': 'body',
                    'metadata': metadata
                })
                chunk_index += 1
                current_chunk_parts = []
                current_tokens = 0

            # Split the large paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sentence_tokens = estimate_tokens(sentence)
                if current_tokens + sentence_tokens > MAX_CHUNK_SIZE and current_tokens >= MIN_CHUNK_SIZE:
                    chunk_content = " ".join(current_chunk_parts)
                    chunks.append({
                        'chunk_index': chunk_index,
                        'content': chunk_content,
                        'token_estimate': current_tokens,
                        'section': 'body',
                        'metadata': metadata
                    })
                    chunk_index += 1
                    # Keep some overlap
                    overlap_parts = current_chunk_parts[-2:] if len(current_chunk_parts) > 2 else []
                    current_chunk_parts = overlap_parts
                    current_tokens = sum(estimate_tokens(p) for p in current_chunk_parts)

                current_chunk_parts.append(sentence)
                current_tokens += sentence_tokens
        else:
            # Normal paragraph handling
            if current_tokens + para_tokens > MAX_CHUNK_SIZE and current_tokens >= MIN_CHUNK_SIZE:
                chunk_content = "\n\n".join(current_chunk_parts)
                chunks.append({
                    'chunk_index': chunk_index,
                    'content': chunk_content,
                    'token_estimate': current_tokens,
                    'section': 'body',
                    'metadata': metadata
                })
                chunk_index += 1
                # Keep last paragraph for overlap
                current_chunk_parts = current_chunk_parts[-1:] if current_chunk_parts else []
                current_tokens = sum(estimate_tokens(p) for p in current_chunk_parts)

            current_chunk_parts.append(para)
            current_tokens += para_tokens

    # Don't forget the last chunk
    if current_tokens >= MIN_CHUNK_SIZE:
        chunk_content = "\n\n".join(current_chunk_parts)
        chunks.append({
            'chunk_index': chunk_index,
            'content': chunk_content,
            'token_estimate': current_tokens,
            'section': 'body',
            'metadata': metadata
        })

    return chunks


def chunk_document(doc_data: dict) -> List[dict]:
    """
    Chunk a document based on its type.

    Args:
        doc_data: Extracted document data (from html_extractor or pdf_extractor)

    Returns:
        List of chunk dictionaries
    """
    doc_type = doc_data.get('document_type', 'unknown')
    clip_id = doc_data.get('clip_id', 'unknown')
    source_url = doc_data.get('source_url', '')
    content = doc_data.get('content', '')

    # Base metadata for all chunks
    base_metadata = {
        'document_type': doc_type,
        'clip_id': clip_id,
        'source_url': source_url
    }

    # Add header for agendas
    if 'header' in doc_data:
        base_metadata['header'] = doc_data['header']

    # Choose chunking strategy based on document type
    if doc_type == 'agenda' and 'sections' in doc_data:
        # Use section-based chunking for agendas
        chunks = chunk_by_sections(content, doc_data['sections'], base_metadata)
    else:
        # Use paragraph-based chunking for minutes and other documents
        chunks = chunk_by_paragraphs(content, base_metadata)

    # Add document-level metadata to each chunk
    for i, chunk in enumerate(chunks):
        chunk['document_id'] = f"{doc_type}_{clip_id}"
        chunk['chunk_id'] = f"{doc_type}_{clip_id}_chunk_{i:03d}"
        chunk['total_chunks'] = len(chunks)

    return chunks


def save_chunks(chunks: List[dict], output_dir: Optional[Path] = None) -> Path:
    """Save chunks to JSON file."""
    output_dir = output_dir or CHUNKS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if not chunks:
        return None

    # Get document ID from first chunk
    doc_id = chunks[0].get('document_id', 'unknown')
    filename = f"{doc_id}_chunks.json"
    output_path = output_dir / filename

    output_data = {
        'document_id': doc_id,
        'chunk_count': len(chunks),
        'chunked_at': datetime.now().isoformat() + 'Z',
        'chunks': chunks
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return output_path


def chunk_all_documents(processed_dir: Optional[Path] = None,
                        output_dir: Optional[Path] = None) -> dict:
    """
    Chunk all processed documents.

    Returns:
        dict: Summary statistics
    """
    processed_dir = processed_dir or PROCESSED_DIR
    output_dir = output_dir or CHUNKS_DIR

    stats = {
        'documents_processed': 0,
        'total_chunks': 0,
        'agenda_chunks': 0,
        'minutes_chunks': 0,
        'errors': []
    }

    # Find all processed documents
    for json_file in processed_dir.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)

            chunks = chunk_document(doc_data)

            if chunks:
                save_chunks(chunks, output_dir)
                stats['documents_processed'] += 1
                stats['total_chunks'] += len(chunks)

                doc_type = doc_data.get('document_type', 'unknown')
                if doc_type == 'agenda':
                    stats['agenda_chunks'] += len(chunks)
                elif doc_type == 'minutes':
                    stats['minutes_chunks'] += len(chunks)

                print(f"Chunked {json_file.name}: {len(chunks)} chunks")

        except Exception as e:
            stats['errors'].append({'file': str(json_file), 'error': str(e)})
            print(f"Error chunking {json_file.name}: {e}")

    return stats


if __name__ == '__main__':
    print("=" * 60)
    print("CCSF Board Document Chunking")
    print("=" * 60)

    stats = chunk_all_documents()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Documents processed: {stats['documents_processed']}")
    print(f"Total chunks:        {stats['total_chunks']}")
    print(f"  Agenda chunks:     {stats['agenda_chunks']}")
    print(f"  Minutes chunks:    {stats['minutes_chunks']}")
    print(f"Errors:              {len(stats['errors'])}")

    if stats['errors']:
        print("\nErrors:")
        for err in stats['errors']:
            print(f"  {err['file']}: {err['error']}")

    print(f"\nChunks saved to: {CHUNKS_DIR}")
