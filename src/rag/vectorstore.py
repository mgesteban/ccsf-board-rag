"""
Vector Store Module for CCSF Board RAG

Uses ChromaDB for vector storage and HuggingFace embeddings.
"""

import json
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings


# Configuration
CHROMA_DIR = Path(__file__).parent.parent.parent / "chroma_db"
CHUNKS_DIR = Path(__file__).parent.parent.parent / "data" / "chunks"
COLLECTION_NAME = "ccsf_board_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality, 384 dimensions


class VectorStore:
    """ChromaDB vector store for CCSF board documents."""

    def __init__(self, persist_directory: Optional[Path] = None,
                 collection_name: str = COLLECTION_NAME):
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory or CHROMA_DIR
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection with default embedding function
        # ChromaDB will use its default embedding (all-MiniLM-L6-v2)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "CCSF Board of Trustees meeting documents"}
        )

        print(f"Vector store initialized: {self.persist_directory}")
        print(f"Collection: {collection_name}")
        print(f"Current document count: {self.collection.count()}")

    def add_chunks(self, chunks: List[dict]) -> int:
        """
        Add chunks to the vector store.

        Args:
            chunks: List of chunk dictionaries with 'content', 'chunk_id', and 'metadata'

        Returns:
            int: Number of chunks added
        """
        if not chunks:
            return 0

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = chunk.get('chunk_id', '')
            content = chunk.get('content', '')

            # Skip if no content
            if not content.strip():
                continue

            # Build metadata (ChromaDB requires flat structure with simple types)
            metadata = {
                'document_id': chunk.get('document_id', ''),
                'document_type': chunk.get('metadata', {}).get('document_type', ''),
                'clip_id': chunk.get('metadata', {}).get('clip_id', ''),
                'section': chunk.get('section', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'total_chunks': chunk.get('total_chunks', 1),
                'source_url': chunk.get('metadata', {}).get('source_url', '')
            }

            ids.append(chunk_id)
            documents.append(content)
            metadatas.append(metadata)

        # Add to collection (ChromaDB handles embedding automatically)
        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

        return len(ids)

    def query(self, query_text: str, n_results: int = 5,
              filter_dict: Optional[dict] = None) -> List[dict]:
        """
        Query the vector store for similar documents.

        Args:
            query_text: The query string
            n_results: Number of results to return
            filter_dict: Optional metadata filter

        Returns:
            List of result dictionaries with content, metadata, and distance
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_dict
        )

        # Format results
        formatted_results = []
        if results and results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    'chunk_id': chunk_id,
                    'content': results['documents'][0][i] if results['documents'] else '',
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })

        return formatted_results

    def get_stats(self) -> dict:
        """Get statistics about the vector store."""
        count = self.collection.count()

        # Get a sample to check metadata
        sample = self.collection.peek(limit=10)

        doc_types = {}
        if sample and sample['metadatas']:
            for meta in sample['metadatas']:
                doc_type = meta.get('document_type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        return {
            'total_chunks': count,
            'collection_name': self.collection.name,
            'persist_directory': str(self.persist_directory),
            'sample_doc_types': doc_types
        }

    def clear(self):
        """Clear all documents from the collection."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name,
            metadata={"description": "CCSF Board of Trustees meeting documents"}
        )
        print("Collection cleared")


def load_all_chunks(chunks_dir: Optional[Path] = None) -> List[dict]:
    """Load all chunks from the chunks directory."""
    chunks_dir = chunks_dir or CHUNKS_DIR

    all_chunks = []
    for chunk_file in chunks_dir.glob('*_chunks.json'):
        with open(chunk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chunks = data.get('chunks', [])
            all_chunks.extend(chunks)

    return all_chunks


def build_vectorstore(chunks_dir: Optional[Path] = None,
                      persist_dir: Optional[Path] = None,
                      clear_existing: bool = False) -> VectorStore:
    """
    Build the vector store from all chunks.

    Args:
        chunks_dir: Directory containing chunk files
        persist_dir: Directory to persist the vector store
        clear_existing: Whether to clear existing data

    Returns:
        VectorStore: The populated vector store
    """
    print("=" * 60)
    print("Building Vector Store")
    print("=" * 60)

    # Initialize vector store
    vs = VectorStore(persist_directory=persist_dir)

    if clear_existing:
        vs.clear()

    # Load all chunks
    print("\nLoading chunks...")
    all_chunks = load_all_chunks(chunks_dir)
    print(f"Loaded {len(all_chunks)} chunks")

    # Add to vector store
    print("\nAdding to vector store...")
    added = vs.add_chunks(all_chunks)
    print(f"Added {added} chunks")

    # Print stats
    stats = vs.get_stats()
    print("\n" + "=" * 60)
    print("Vector Store Stats")
    print("=" * 60)
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Collection: {stats['collection_name']}")
    print(f"Persist directory: {stats['persist_directory']}")

    return vs


if __name__ == '__main__':
    # Build the vector store
    vs = build_vectorstore(clear_existing=True)

    # Test a query
    print("\n" + "=" * 60)
    print("Test Query: 'parking fees'")
    print("=" * 60)

    results = vs.query("parking fees", n_results=3)
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} (distance: {result['distance']:.4f}) ---")
        print(f"Document: {result['metadata'].get('document_id', 'N/A')}")
        print(f"Section: {result['metadata'].get('section', 'N/A')}")
        print(f"Content: {result['content'][:200]}...")
