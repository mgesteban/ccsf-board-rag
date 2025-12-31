"""
RAG Query Engine for CCSF Board Documents

Connects the vector store to Claude for question answering.
"""

import os
from pathlib import Path
from typing import List, Optional

from anthropic import Anthropic
from dotenv import load_dotenv

try:
    from .vectorstore import VectorStore
except ImportError:
    from vectorstore import VectorStore

# Load environment variables
load_dotenv()

# Configuration
LLM_MODEL = "claude-sonnet-4-20250514"
TEMPERATURE = 0.3
MAX_TOKENS = 1024
TOP_K_RETRIEVAL = 5

SYSTEM_PROMPT = """You are a helpful assistant answering questions about City College of San Francisco (CCSF) Board of Trustees meetings.

INSTRUCTIONS:
1. Use ONLY the provided context from board meeting documents
2. If the answer isn't in the context, say "I don't have information about that in the board meeting documents I have access to."
3. Always cite which meeting date(s) or document(s) your information comes from
4. Be specific and factual
5. If asked about current status of something, note that your information is only as recent as the latest meeting in the documents
6. When mentioning agenda items or motions, include the item number if available

CONTEXT FROM BOARD DOCUMENTS:
{context}"""


class RAGQueryEngine:
    """RAG query engine using Claude and ChromaDB vector store."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize the query engine.

        Args:
            vector_store: Optional VectorStore instance. Creates one if not provided.
        """
        self.vector_store = vector_store or VectorStore()

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Please set it in your .env file."
            )
        self.client = Anthropic(api_key=api_key)

        print(f"RAG Query Engine initialized")
        print(f"Model: {LLM_MODEL}")
        print(f"Vector store documents: {self.vector_store.collection.count()}")

    def retrieve(self, query: str, n_results: int = TOP_K_RETRIEVAL) -> List[dict]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The user's question
            n_results: Number of results to retrieve

        Returns:
            List of relevant chunks with content and metadata
        """
        return self.vector_store.query(query, n_results=n_results)

    def format_context(self, chunks: List[dict]) -> str:
        """Format retrieved chunks into context string for the prompt."""
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            doc_type = metadata.get('document_type', 'document')
            doc_id = metadata.get('document_id', 'unknown')
            section = metadata.get('section', '')
            clip_id = metadata.get('clip_id', '')

            # Build source reference
            source_ref = f"[{doc_type.upper()}]"
            if clip_id:
                source_ref += f" Meeting {clip_id}"
            if section:
                source_ref += f" - {section}"

            context_parts.append(
                f"--- Document {i} {source_ref} ---\n{chunk['content']}"
            )

        return "\n\n".join(context_parts)

    def query(self, question: str, n_results: int = TOP_K_RETRIEVAL,
              return_sources: bool = True) -> dict:
        """
        Answer a question using RAG.

        Args:
            question: The user's question
            n_results: Number of documents to retrieve
            return_sources: Whether to include source documents in response

        Returns:
            dict with 'answer', 'sources' (if requested), and 'usage'
        """
        # Retrieve relevant documents
        chunks = self.retrieve(question, n_results=n_results)

        if not chunks:
            return {
                'answer': "I couldn't find any relevant information in the board meeting documents.",
                'sources': [],
                'usage': None
            }

        # Format context
        context = self.format_context(chunks)

        # Create the prompt with context
        system = SYSTEM_PROMPT.format(context=context)

        # Call Claude
        response = self.client.messages.create(
            model=LLM_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system,
            messages=[
                {"role": "user", "content": question}
            ]
        )

        # Extract answer
        answer = response.content[0].text

        # Build response
        result = {
            'answer': answer,
            'usage': {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            }
        }

        if return_sources:
            result['sources'] = [
                {
                    'chunk_id': chunk.get('chunk_id', ''),
                    'document_type': chunk.get('metadata', {}).get('document_type', ''),
                    'section': chunk.get('metadata', {}).get('section', ''),
                    'distance': chunk.get('distance', 0),
                    'content_preview': chunk['content'][:200] + '...'
                }
                for chunk in chunks
            ]

        return result

    def chat(self, messages: List[dict], n_results: int = TOP_K_RETRIEVAL) -> dict:
        """
        Multi-turn chat with RAG context.

        Args:
            messages: List of message dicts with 'role' and 'content'
            n_results: Number of documents to retrieve for context

        Returns:
            dict with 'answer', 'sources', and 'usage'
        """
        # Get the latest user message for retrieval
        user_messages = [m for m in messages if m['role'] == 'user']
        if not user_messages:
            return {'answer': "Please ask a question.", 'sources': [], 'usage': None}

        latest_question = user_messages[-1]['content']

        # Retrieve context based on latest question
        chunks = self.retrieve(latest_question, n_results=n_results)
        context = self.format_context(chunks) if chunks else "No relevant documents found."

        # Create system prompt with context
        system = SYSTEM_PROMPT.format(context=context)

        # Call Claude with full conversation
        response = self.client.messages.create(
            model=LLM_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system,
            messages=messages
        )

        answer = response.content[0].text

        return {
            'answer': answer,
            'sources': [
                {
                    'chunk_id': chunk.get('chunk_id', ''),
                    'document_type': chunk.get('metadata', {}).get('document_type', ''),
                    'section': chunk.get('metadata', {}).get('section', ''),
                    'distance': chunk.get('distance', 0)
                }
                for chunk in chunks
            ],
            'usage': {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            }
        }


def create_query_engine() -> RAGQueryEngine:
    """Factory function to create a query engine with defaults."""
    return RAGQueryEngine()


if __name__ == '__main__':
    # Test the query engine
    print("=" * 60)
    print("Testing RAG Query Engine")
    print("=" * 60)

    try:
        engine = create_query_engine()

        # Test questions
        test_questions = [
            "What travel requests were approved recently?",
            "What is the Strong Workforce Program?",
            "Who is on the Board of Trustees?",
        ]

        for question in test_questions:
            print(f"\n{'=' * 60}")
            print(f"Question: {question}")
            print("=" * 60)

            result = engine.query(question)

            print(f"\nAnswer:\n{result['answer']}")

            if result.get('sources'):
                print(f"\nSources ({len(result['sources'])}):")
                for source in result['sources'][:3]:
                    print(f"  - {source['document_type']}: {source['section'][:50]}...")

            if result.get('usage'):
                print(f"\nTokens: {result['usage']['input_tokens']} in, {result['usage']['output_tokens']} out")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure ANTHROPIC_API_KEY is set in your .env file")
