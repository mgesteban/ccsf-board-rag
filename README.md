# CCSF Board RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that answers questions about City College of San Francisco (CCSF) Board of Trustees meetings using scraped agendas and minutes.

## Overview

This project scrapes board meeting documents from the [CCSF Granicus archive](https://ccsf.granicus.com/ViewPublisher.php?view_id=3), processes them into searchable chunks, and provides a conversational interface powered by Claude to answer questions about board meetings.

**Data Coverage:**
- 196 board meetings (February 2006 - December 2025)
- 196 meeting agendas
- 190 meeting minutes

## Features

- Web scraping of Granicus archive for meeting agendas and minutes
- PDF text extraction for minutes documents
- HTML content extraction for agenda pages
- Vector-based semantic search using ChromaDB
- Natural language Q&A powered by Claude API
- Streamlit web interface for easy interaction

## Technology Stack

| Component | Technology |
|-----------|------------|
| Web Scraping | Playwright, BeautifulSoup |
| PDF Processing | PyMuPDF (fitz) |
| Vector Database | ChromaDB |
| Embeddings | all-MiniLM-L6-v2 |
| LLM | Claude API (Anthropic) |
| Web Interface | Streamlit |

## Installation

### Prerequisites

- Python 3.9 or higher
- An Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/mgesteban/ccsf-board-rag.git
   cd ccsf-board-rag
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

## Usage

### Data Pipeline

Run the scripts in order to build the knowledge base:

```bash
# Step 1: Discover document URLs from Granicus archive
python scripts/01_discover_urls.py

# Step 2: Download and extract text from documents
python scripts/02_extract_documents.py

# Step 3: Build the vector store with embeddings
python scripts/03_build_vectorstore.py

# Step 4: Launch the Streamlit app
python scripts/04_run_app.py
# Or: streamlit run src/app/streamlit_app.py
```

### Example Questions

Once the app is running, you can ask questions like:

- "What was discussed about student parking fees?"
- "When did the board approve the 2024 budget?"
- "What motions were passed in January 2024?"
- "Who spoke during public comment on October 23, 2025?"

## Project Structure

```
ccsf-board-rag/
├── README.md               # This file
├── CLAUDE.md               # Development documentation
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
│
├── src/
│   ├── scraper/            # Web scraping modules
│   │   ├── url_discovery.py
│   │   ├── html_extractor.py
│   │   └── pdf_extractor.py
│   ├── processing/         # Text processing
│   │   └── chunker.py
│   ├── rag/                # RAG components
│   │   ├── vectorstore.py
│   │   └── query_engine.py
│   └── app/                # Web interface
│       └── streamlit_app.py
│
├── scripts/                # Pipeline scripts
│   ├── 01_discover_urls.py
│   ├── 02_extract_documents.py
│   ├── 03_build_vectorstore.py
│   └── 04_run_app.py
│
├── data/
│   ├── document_urls.json  # Discovered meeting URLs
│   ├── raw/                # Downloaded PDFs (gitignored)
│   ├── processed/          # Extracted text (gitignored)
│   └── chunks/             # Chunked documents (gitignored)
│
└── tests/                  # Test files
```

## Data Sources

All data is sourced from publicly available CCSF Board of Trustees meeting records:

- **Source:** [CCSF Granicus Archive](https://ccsf.granicus.com/ViewPublisher.php?view_id=3)
- **Document Types:** Meeting agendas (HTML) and minutes (PDF)
- **Date Range:** February 2006 - Present

## Development

This project was developed using Claude Code. See `CLAUDE.md` for detailed development documentation including:

- Implementation phases and status
- Technical decisions and rationale
- Session notes and discovered information
- Troubleshooting guides

## License

This project is for educational and research purposes. Board meeting documents are public records of the City College of San Francisco.

## Acknowledgments

- City College of San Francisco Board of Trustees for making meeting records publicly available
- [Andrew Ng](https://www.andrewng.org/) and [DeepLearning.AI](https://www.deeplearning.ai/) for providing world-class AI education
- [Elie Schoppik](https://www.linkedin.com/in/eschoppik/) of Anthropic for teaching the excellent [Claude Code: A Highly Agentic Coding Assistant](https://learn.deeplearning.ai/courses/claude-code-a-highly-agentic-coding-assistant) course that made this project possible
- Built with Claude Code by Anthropic
