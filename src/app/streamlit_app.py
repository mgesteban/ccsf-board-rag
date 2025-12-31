"""
CCSF Board Meetings Assistant - Streamlit Chat Interface

A RAG-powered chatbot for querying City College of San Francisco
Board of Trustees meeting documents.
"""

import sys
from pathlib import Path

import streamlit as st

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from rag.query_engine import RAGQueryEngine
from rag.vectorstore import VectorStore

# Page configuration
st.set_page_config(
    page_title="CCSF Board Meetings Assistant",
    page_icon="graduation_cap",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'query_engine' not in st.session_state:
    st.session_state.query_engine = None

if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = {'input': 0, 'output': 0}


@st.cache_resource
def load_query_engine():
    """Load the RAG query engine (cached)."""
    return RAGQueryEngine()


def initialize_engine():
    """Initialize the query engine with error handling."""
    try:
        st.session_state.query_engine = load_query_engine()
        return True
    except Exception as e:
        st.error(f"Failed to initialize query engine: {e}")
        return False


# Sidebar
with st.sidebar:
    st.title("About")
    st.markdown("""
    This chatbot answers questions about **City College of San Francisco
    (CCSF) Board of Trustees** meetings.

    **Data Source:** CCSF Granicus Archive

    The chatbot uses RAG (Retrieval-Augmented Generation) to find
    relevant information from board meeting agendas and minutes,
    then uses Claude to generate accurate answers.
    """)

    st.divider()

    # Stats
    st.subheader("Database Stats")
    if st.session_state.query_engine:
        stats = st.session_state.query_engine.vector_store.get_stats()
        st.metric("Total Documents", stats['total_chunks'])
        st.caption(f"Collection: {stats['collection_name']}")
    else:
        st.caption("Loading...")

    st.divider()

    # Example questions
    st.subheader("Example Questions")
    example_questions = [
        "What travel requests were recently approved?",
        "Who are the current Board of Trustees members?",
        "What consent items were discussed?",
        "What is the Strong Workforce Program?",
        "What facilities projects are underway?",
    ]

    for q in example_questions:
        if st.button(q, key=f"example_{q[:20]}"):
            st.session_state.pending_question = q

    st.divider()

    # Controls
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.total_tokens = {'input': 0, 'output': 0}
        st.rerun()

    # Token usage
    if st.session_state.total_tokens['input'] > 0:
        st.subheader("Token Usage")
        st.caption(f"Input: {st.session_state.total_tokens['input']:,}")
        st.caption(f"Output: {st.session_state.total_tokens['output']:,}")


# Main content
st.title("CCSF Board Meetings Assistant")
st.caption("Ask questions about City College of San Francisco Board of Trustees meetings")

# Initialize query engine
if st.session_state.query_engine is None:
    with st.spinner("Loading RAG system..."):
        if not initialize_engine():
            st.stop()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show sources for assistant messages
        if message["role"] == "assistant" and "sources" in message:
            sources = message["sources"]
            if sources:
                with st.expander(f"View Sources ({len(sources)})"):
                    for i, source in enumerate(sources, 1):
                        doc_type = source.get('document_type', 'document').upper()
                        section = source.get('section', 'N/A')
                        distance = source.get('distance', 0)
                        st.markdown(f"**{i}. [{doc_type}]** {section}")
                        st.caption(f"Relevance score: {1 - distance:.2%}")


# Handle pending question from sidebar
if 'pending_question' in st.session_state:
    question = st.session_state.pending_question
    del st.session_state.pending_question

    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    # Get response
    with st.spinner("Searching documents and generating response..."):
        result = st.session_state.query_engine.query(question)

    # Add assistant message with sources
    st.session_state.messages.append({
        "role": "assistant",
        "content": result['answer'],
        "sources": result.get('sources', [])
    })

    # Update token count
    if result.get('usage'):
        st.session_state.total_tokens['input'] += result['usage']['input_tokens']
        st.session_state.total_tokens['output'] += result['usage']['output_tokens']

    st.rerun()


# Chat input
if prompt := st.chat_input("Ask a question about CCSF board meetings..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating response..."):
            result = st.session_state.query_engine.query(prompt)

        st.markdown(result['answer'])

        # Show sources
        sources = result.get('sources', [])
        if sources:
            with st.expander(f"View Sources ({len(sources)})"):
                for i, source in enumerate(sources, 1):
                    doc_type = source.get('document_type', 'document').upper()
                    section = source.get('section', 'N/A')
                    distance = source.get('distance', 0)
                    st.markdown(f"**{i}. [{doc_type}]** {section}")
                    st.caption(f"Relevance score: {1 - distance:.2%}")

    # Store message with sources
    st.session_state.messages.append({
        "role": "assistant",
        "content": result['answer'],
        "sources": sources
    })

    # Update token count
    if result.get('usage'):
        st.session_state.total_tokens['input'] += result['usage']['input_tokens']
        st.session_state.total_tokens['output'] += result['usage']['output_tokens']
