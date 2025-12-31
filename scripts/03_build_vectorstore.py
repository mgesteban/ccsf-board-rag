#!/usr/bin/env python3
"""
Step 3: Build Vector Store

This script builds the ChromaDB vector store from chunked documents.
It loads all chunk files and creates embeddings for semantic search.

Usage:
    python scripts/03_build_vectorstore.py [options]

Options:
    --clear         Clear existing vector store before adding
    --query TEXT    Run a test query after building
    --stats         Show stats only, don't rebuild
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag.vectorstore import VectorStore, build_vectorstore, load_all_chunks


def main():
    parser = argparse.ArgumentParser(
        description="Build vector store from chunked documents"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing vector store before adding"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Run a test query after building"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show stats only, don't rebuild"
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=5,
        help="Number of results for test query (default: 5)"
    )

    args = parser.parse_args()

    if args.stats:
        # Just show stats
        print("=" * 60)
        print("Vector Store Stats")
        print("=" * 60)
        vs = VectorStore()
        stats = vs.get_stats()
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Collection: {stats['collection_name']}")
        print(f"Persist directory: {stats['persist_directory']}")
        print(f"Sample doc types: {stats['sample_doc_types']}")
        return

    # Build the vector store
    vs = build_vectorstore(clear_existing=args.clear)

    # Run test query if specified
    if args.query:
        print("\n" + "=" * 60)
        print(f"Test Query: '{args.query}'")
        print("=" * 60)

        results = vs.query(args.query, n_results=args.n_results)

        if not results:
            print("No results found.")
        else:
            for i, result in enumerate(results):
                print(f"\n--- Result {i+1} (distance: {result['distance']:.4f}) ---")
                print(f"Document: {result['metadata'].get('document_id', 'N/A')}")
                print(f"Type: {result['metadata'].get('document_type', 'N/A')}")
                print(f"Section: {result['metadata'].get('section', 'N/A')}")
                content_preview = result['content'][:300].replace('\n', ' ')
                print(f"Content: {content_preview}...")

    print("\n" + "=" * 60)
    print("Vector store build complete!")
    print("=" * 60)
    print(f"Ready for RAG queries.")
    print(f"Collection: {vs.collection.name}")
    print(f"Total documents: {vs.collection.count()}")


if __name__ == "__main__":
    main()
