# CLAUDE.md - CCSF Board RAG Chatbot Project

> **This file serves as persistent memory and instructions for Claude Code.**
> **Read this file at the start of every session to understand the project context.**

---

## Project Overview

**Goal**: Build a RAG (Retrieval-Augmented Generation) chatbot that answers questions about City College of San Francisco (CCSF) Board of Trustees meetings using scraped agendas and minutes.

**Data Sources**:
- HTML Agendas from CCSF Granicus: `https://ccsf.granicus.com/ViewPublisher.php?view_id=3`
- PDF Minutes from the same archive

**End User**: Someone who wants to quickly find information from board meetings without reading through hundreds of documents.

---

## Technology Stack

| Component | Technology | Why This Choice |
|-----------|------------|-----------------|
| **Web Scraping** | Playwright (via MCP) | Handles JavaScript-rendered Granicus pages |
| **PDF Extraction** | PyMuPDF (fitz) | Fast, accurate PDF text extraction |
| **RAG Framework** | LlamaIndex | Beginner-friendly, great documentation |
| **Vector Database** | ChromaDB | Local, no setup, persistent storage |
| **Embeddings** | HuggingFace BGE | Free, runs locally, high quality |
| **LLM** | Claude API (Sonnet) | High quality responses, good at following instructions |
| **Web Interface** | Streamlit (via MCP) | Rapid prototyping, minimal frontend code |
| **MCP Servers** | Playwright, Streamlit | Enhanced capabilities for scraping and UI |

---

## Project Structure

```
ccsf-board-rag/
├── CLAUDE.md                     # THIS FILE - Project memory for Claude Code
├── README.md                     # User-facing documentation
├── requirements.txt              # Python dependencies
├── .env                          # API keys (gitignored)
├── .env.example                  # Template for .env
├── .gitignore                    # Git ignore rules
│
├── src/
│   ├── __init__.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── url_discovery.py      # Find all document URLs from Granicus
│   │   ├── html_extractor.py     # Extract text from agenda HTML pages
│   │   └── pdf_extractor.py      # Extract text from minutes PDFs
│   ├── processing/
│   │   ├── __init__.py
│   │   └── chunker.py            # Split documents into chunks for RAG
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── vectorstore.py        # ChromaDB setup and operations
│   │   └── query_engine.py       # LlamaIndex RAG logic with Claude
│   └── app/
│       ├── __init__.py
│       └── streamlit_app.py      # Chat interface
│
├── data/
│   ├── raw/                      # Downloaded PDFs (gitignored)
│   ├── processed/                # Extracted text as JSON (gitignored)
│   ├── chunks/                   # Chunked documents (gitignored)
│   └── document_urls.json        # Discovered URLs (committed)
│
├── chroma_db/                    # Vector database storage (gitignored)
│
├── scripts/
│   ├── 01_discover_urls.py       # Step 1: Find all document URLs
│   ├── 02_extract_documents.py   # Step 2: Download and extract text
│   ├── 03_build_vectorstore.py   # Step 3: Create embeddings and index
│   └── 04_run_app.py             # Step 4: Launch Streamlit app
│
└── tests/
    ├── __init__.py
    ├── test_scraper.py
    ├── test_chunker.py
    └── test_rag.py
```

---

## MCP Server Integration

### Playwright MCP Server
**Purpose**: Browser automation for scraping JavaScript-heavy Granicus pages

**When to Use**:
- Navigating the Granicus archive (may have JavaScript pagination)
- Clicking through to agenda/minutes pages
- Handling any dynamic content loading
- Taking screenshots for debugging

**Key Capabilities**:
- `playwright_navigate` - Go to a URL
- `playwright_screenshot` - Capture page state
- `playwright_click` - Click elements
- `playwright_fill` - Enter text in forms
- `playwright_evaluate` - Run JavaScript on page
- `playwright_get_text` - Extract text content

**Example Usage Pattern**:
```
1. Navigate to archive page
2. Wait for content to load (may need JavaScript execution)
3. Extract meeting list
4. For each meeting, navigate and extract agenda/minutes URLs
5. Handle pagination by clicking "next" or loading more
```

### Streamlit MCP Server
**Purpose**: Enhanced Streamlit app development and management

**When to Use**:
- Creating and modifying the Streamlit interface
- Running the Streamlit app
- Debugging UI issues
- Hot-reloading during development

**Key Capabilities**:
- Running Streamlit apps
- Managing app state
- Handling file uploads in the UI

---

## Implementation Phases

### Phase 1: Project Setup [COMPLETE]
**Status**: Complete

**Tasks**:
- [x] Create project directory structure
- [x] Set up virtual environment (Python 3.11)
- [x] Install dependencies from requirements.txt
- [x] Create .env with ANTHROPIC_API_KEY
- [x] Verify MCP servers are available (Playwright, Streamlit)

**Verification**:
```bash
# Test that imports work - PASSED
python -c "import chromadb; import llama_index; import anthropic; import streamlit; import fitz; print('OK')"
```

---

### Phase 2: URL Discovery [COMPLETE]
**Status**: Complete

**Goal**: Scrape the Granicus archive to find all agenda and minutes URLs

**Key File**: `src/scraper/url_discovery.py`

**Approach**:
1. Use Playwright MCP to navigate to archive page
2. Handle JavaScript-loaded content (Granicus often uses JS)
3. Extract all meeting entries with dates, agenda URLs, minutes URLs
4. Save to `data/document_urls.json`

**Granicus Page Structure** (investigate and update):
```
- Archive URL: https://ccsf.granicus.com/ViewPublisher.php?view_id=3
- Meeting list: [TBD - inspect page structure]
- Agenda links: [TBD - usually .html or ViewAgenda.php]
- Minutes links: [TBD - usually .pdf]
- Pagination: [TBD - may be JavaScript-based]
```

**Output Schema**:
```json
{
  "scraped_at": "2024-01-15T10:30:00Z",
  "source_url": "https://ccsf.granicus.com/ViewPublisher.php?view_id=3",
  "total_meetings": 150,
  "meetings": [
    {
      "meeting_id": "meeting_2024_01_15",
      "date": "2024-01-15",
      "title": "Regular Meeting",
      "agenda_url": "https://...",
      "minutes_url": "https://...",
      "video_url": "https://..." 
    }
  ]
}
```

**Verification**:
- [x] document_urls.json exists and has data (196 meetings)
- [x] Spot-check 3 URLs manually in browser
- [x] Count is reasonable (196 meetings from 2006-2025)

---

### Phase 3: Document Extraction [PENDING]
**Status**: Not Started

**Goal**: Download PDFs and extract text from all agendas and minutes

**Key Files**:
- `src/scraper/html_extractor.py` - For agenda HTML pages
- `src/scraper/pdf_extractor.py` - For minutes PDFs

**HTML Extraction Strategy**:
- Use BeautifulSoup or Playwright to get page content
- Remove navigation, headers, footers, scripts
- Preserve document structure (agenda item numbers, sections)
- Handle encoding issues

**PDF Extraction Strategy**:
- Download PDF to `data/raw/`
- Use PyMuPDF (fitz) for text extraction
- Handle multi-column layouts
- Detect and warn about scanned PDFs (would need OCR)

**Output Schema** (per document):
```json
{
  "document_id": "meeting_2024_01_15_agenda",
  "source_url": "https://...",
  "document_type": "agenda",
  "meeting_date": "2024-01-15",
  "title": "Regular Meeting - Agenda",
  "content": "Full extracted text...",
  "extraction_timestamp": "2024-01-20T15:00:00Z",
  "metadata": {
    "page_count": 5,
    "character_count": 15000,
    "local_file_path": "data/raw/meeting_2024_01_15_minutes.pdf"
  }
}
```

**Verification**:
- [ ] Processed JSON files exist in `data/processed/`
- [ ] Text content is readable (not garbled)
- [ ] Metadata is populated
- [ ] Error log shows any failed extractions

---

### Phase 4: Text Chunking [PENDING]
**Status**: Not Started

**Goal**: Split documents into smaller chunks suitable for RAG retrieval

**Key File**: `src/processing/chunker.py`

**Chunking Strategy**:
```
Primary: Semantic chunking by document structure
- Agenda items (numbered sections)
- Major topic boundaries
- Natural paragraph breaks

Fallback: Recursive character splitting
- Target: ~500 tokens per chunk
- Overlap: ~50 tokens
- Split hierarchy: paragraphs → sentences → words
```

**Chunk Schema**:
```json
{
  "chunk_id": "meeting_2024_01_15_agenda_chunk_003",
  "document_id": "meeting_2024_01_15_agenda",
  "document_type": "agenda",
  "meeting_date": "2024-01-15",
  "chunk_index": 3,
  "total_chunks": 12,
  "content": "Chunk text content...",
  "token_count": 487
}
```

**Verification**:
- [ ] Chunks are reasonable size (300-600 tokens)
- [ ] Chunks don't cut off mid-sentence
- [ ] Metadata is correctly propagated

---

### Phase 5: Vector Store Setup [PENDING]
**Status**: Not Started

**Goal**: Create embeddings and store in ChromaDB for similarity search

**Key File**: `src/rag/vectorstore.py`

**Configuration**:
```python
# Embedding model
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # 384 dimensions, good quality

# ChromaDB settings
COLLECTION_NAME = "ccsf_board_documents"
PERSIST_DIRECTORY = "./chroma_db"

# Search settings
DEFAULT_TOP_K = 5
```

**Functions to Implement**:
```python
def initialize_vectorstore() -> VectorStore:
    """Create or load ChromaDB collection with embeddings"""

def add_documents(chunks: List[dict]) -> int:
    """Add chunks to vector store, return count added"""

def query_similar(query: str, top_k: int = 5) -> List[dict]:
    """Find most similar chunks to query"""

def get_stats() -> dict:
    """Return collection statistics"""
```

**Verification**:
- [ ] `chroma_db/` folder has data files
- [ ] Can query and get relevant results
- [ ] Stats show expected document count

---

### Phase 6: RAG Query Engine [PENDING]
**Status**: Not Started

**Goal**: Connect retrieval to Claude for question answering

**Key File**: `src/rag/query_engine.py`

**System Prompt**:
```
You are a helpful assistant answering questions about City College of 
San Francisco (CCSF) Board of Trustees meetings.

INSTRUCTIONS:
1. Use ONLY the provided context from board meeting documents
2. If the answer isn't in the context, say "I don't have information about 
   that in the board meeting documents I have access to."
3. Always cite which meeting date(s) your information comes from
4. Be specific and factual
5. If asked about current status of something, note that your information 
   is only as recent as the latest meeting in the documents

CONTEXT FROM BOARD DOCUMENTS:
{context}

USER QUESTION: {question}
```

**Configuration**:
```python
LLM_MODEL = "claude-sonnet-4-20250514"
TEMPERATURE = 0.3  # Lower = more focused/factual
MAX_TOKENS = 1024
TOP_K_RETRIEVAL = 5
```

**Verification**:
- [ ] Test query returns relevant answer
- [ ] Citations are included
- [ ] "I don't know" for out-of-scope questions

---

### Phase 7: Streamlit Interface [PENDING]
**Status**: Not Started

**Goal**: Create user-friendly chat interface

**Key File**: `src/app/streamlit_app.py`

**UI Components**:
```
┌─────────────────────────────────────────────────────────────┐
|  CCSF Board Meetings Assistant                             |
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌────────────────────────────────────┐│
│ │   SIDEBAR       │  │         CHAT AREA                  ││
│ │                 │  │                                    ││
│ │ About this tool │  │  [User]: What was discussed about  ││
│ │                 │  │          student parking?          ││
│ │ Data source:    │  │                                    ││
│ │ CCSF Granicus   │  │  [Assistant]: Based on the board   ││
│ │                 │  │  minutes from Jan 15, 2024...      ││
│ │ Documents:      │  │                                    ││
│ │ 150 meetings    │  │  Sources:                          ││
│ │ 2019-2024       │  │  - Meeting 2024-01-15 (Minutes)    ││
│ │                 │  │  - Meeting 2023-11-20 (Agenda)     ││
│ │ ───────────────│  │                                    ││
│ │ Example Qs:     │  │  ──────────────────────────────── ││
│ │ • Budget 2024   │  │                                    ││
│ │ • Parking fees  │  │  [Input box: Ask a question...]   ││
│ │ • Board members │  │                                    ││
│ └─────────────────┘  └────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Chat history in session state
- Expandable source citations
- Example questions (clickable)
- Clear chat button
- Loading spinner during queries

**Verification**:
- [ ] App launches without errors
- [ ] Can send messages and receive responses
- [ ] Source citations are visible
- [ ] Chat history persists in session

---

### Phase 8: Testing and Refinement [PENDING]
**Status**: Not Started

**Test Cases**:
```python
TEST_QUESTIONS = [
    # Should be answerable
    ("What was the budget for fiscal year 2023?", True),
    ("When did the board discuss parking fees?", True),
    ("What motions were passed in January 2024?", True),
    
    # Should NOT be answerable (hallucination test)
    ("What is the capital of France?", False),
    ("Who won the Super Bowl?", False),
    ("What will happen at the next meeting?", False),
]
```

**Quality Metrics**:
- Relevance: Do retrieved chunks relate to the question?
- Accuracy: Is the answer factually correct per the documents?
- Citation: Does it cite the correct meeting dates?
- Hallucination: Does it refuse to answer out-of-scope questions?

---

## Common Issues and Solutions

### Granicus Scraping Issues
**Problem**: Page content not loading
**Solution**: Use Playwright with wait strategies
```python
# Wait for specific element to appear
await page.wait_for_selector('.meeting-list')
# Or wait for network idle
await page.wait_for_load_state('networkidle')
```

### PDF Extraction Issues
**Problem**: Scanned PDFs return no text
**Solution**: Detect and log, consider OCR later
```python
if len(extracted_text) < 100:
    logger.warning(f"PDF may be scanned: {pdf_path}")
```

### Chunking Issues
**Problem**: Relevant info split across chunks
**Solution**: Increase overlap or use parent-child chunking

### Retrieval Issues
**Problem**: Wrong chunks retrieved
**Solutions**:
- Try different embedding model
- Implement hybrid search (semantic + keyword)
- Add query expansion

---

## Session Notes

### Session Log
Use this section to track progress across Claude Code sessions:

```
2025-12-30 - Session 1
- Completed:
  - Phase 1: Project setup (Python 3.11 venv, all dependencies installed)
  - Phase 2: URL Discovery (196 meetings scraped from Granicus)
  - Implemented src/scraper/url_discovery.py module
  - Created scripts/01_discover_urls.py
  - Saved meeting URLs to data/document_urls.json
- Issues:
  - Original venv was Python 3.6 (too old), recreated with Python 3.11
  - Granicus page has large DOM, used JavaScript evaluation for extraction
- Next: Phase 3 - Document Extraction (download PDFs, extract HTML agendas)
---
```

### Discovered Information
Update this as you learn more about the Granicus site structure:

```
Granicus Page Structure:
- Archive URL: https://ccsf.granicus.com/ViewPublisher.php?view_id=3
- Meetings displayed in <table> with one <tr> per meeting
- Columns: Title | Date | Duration | Agenda | Minutes | Video | Audio
- Agenda links: AgendaViewer.php?view_id=3&clip_id=XXXX
- Minutes links: MinutesViewer.php?view_id=3&clip_id=XXXX&doc_id=YYYY
- All content loads on initial page (no pagination/infinite scroll)

Meeting Types Found:
- "Regular Meeting of the Board of Trustees" (most common)
- Special meetings, study sessions may also exist

Date Range of Documents:
- Earliest: 2006-02-23
- Latest: 2025-12-04
- Total meetings: 196
- With agendas: 196
- With minutes: 190 (6 recent meetings pending)
```

---

## Quick Start Commands

```bash
# Setup (run once)
cd ccsf-board-rag
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to add ANTHROPIC_API_KEY

# Data Pipeline
python scripts/01_discover_urls.py      # Find document URLs
python scripts/02_extract_documents.py  # Extract text
python scripts/03_build_vectorstore.py  # Build index

# Run App
streamlit run src/app/streamlit_app.py
# Or: python scripts/04_run_app.py
```

---

## Learning Resources

**RAG Concepts**:
- Embeddings convert text to vectors that capture meaning
- Similar texts have vectors that are close together
- We retrieve relevant chunks by finding vectors similar to the query
- LLM synthesizes an answer from retrieved context

**Why This Architecture**:
- ChromaDB: Simple, no external services, persists to disk
- LlamaIndex: Handles RAG pipeline complexity, good defaults
- Streamlit: Minimal code for functional UI
- Playwright: Handles modern JavaScript-heavy websites

---

## Important Notes

1. **API Costs**: Claude API has usage costs. Monitor at console.anthropic.com
2. **Rate Limits**: Add delays between API calls to avoid rate limiting
3. **Data Privacy**: Board documents are public, but be mindful of PII
4. **Scraping Ethics**: Use polite delays, respect robots.txt
5. **Storage**: Downloaded PDFs and vector DB can be large (GB+)

---

*Last Updated: 2025-12-30*
*Project Status: Phase 2 Complete - Ready for Phase 3 (Document Extraction)*
