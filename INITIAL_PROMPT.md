# Initial Prompt for Claude Code

Copy and paste the prompt below into Claude Code in VSCode to start your project. Make sure you have the `CLAUDE.md` file in your intended project directory first.

---

## COPY THIS PROMPT TO CLAUDE CODE:

```
I'm building a RAG chatbot for CCSF Board of Trustees meetings. I have a comprehensive project plan in CLAUDE.md - please read it first.

**Project Summary**:
- Scrape agendas (HTML) and minutes (PDFs) from CCSF Granicus archive
- Build a RAG system using LlamaIndex + ChromaDB + Claude API
- Create a Streamlit chat interface

**MCP Servers Available**:
- Playwright MCP: Use this for scraping the Granicus site (it uses JavaScript)
- Streamlit MCP: Use this for the web interface

**Start with Phase 1: Project Setup**

Please:
1. Read the CLAUDE.md file to understand the full project plan
2. Create the project directory structure as specified
3. Create requirements.txt with all needed dependencies
4. Create .env.example showing required API keys
5. Create a comprehensive .gitignore
6. Create a basic README.md

After setup, verify everything works by testing imports.

The Granicus archive URL is: https://ccsf.granicus.com/ViewPublisher.php?view_id=3

Let's build this step by step, completing each phase before moving to the next. Update the CLAUDE.md file's checkboxes and session notes as we progress.
```

---

## Follow-Up Prompts for Each Phase

Save these prompts for later phases:

### Phase 2 Prompt (URL Discovery):
```
Let's work on Phase 2: URL Discovery.

Use the Playwright MCP server to:
1. Navigate to https://ccsf.granicus.com/ViewPublisher.php?view_id=3
2. Take a screenshot so we can see the page structure
3. Inspect the HTML to understand how meetings are listed
4. Identify where agenda and minutes links are located
5. Check if there's pagination and how it works

Then create src/scraper/url_discovery.py that:
- Uses Playwright to scrape all meeting URLs
- Handles any JavaScript-loaded content
- Saves results to data/document_urls.json
- Includes polite delays between requests

Update CLAUDE.md with what we learn about the page structure.
```

### Phase 3 Prompt (Document Extraction):
```
Let's work on Phase 3: Document Extraction.

Create:
1. src/scraper/html_extractor.py - Extract text from agenda HTML pages
2. src/scraper/pdf_extractor.py - Download and extract text from minutes PDFs
3. scripts/02_extract_documents.py - Batch processor for all documents

Requirements:
- Use PyMuPDF for PDF extraction
- Preserve document structure where possible
- Handle errors gracefully (don't stop on failures)
- Save extracted text to data/processed/ as JSON
- Include progress logging
- Support resume capability (skip already-processed files)

Test with a few documents before running the full batch.
```

### Phase 4 Prompt (Chunking):
```
Let's work on Phase 4: Text Chunking.

Create src/processing/chunker.py that:
1. Implements semantic chunking (respects document structure)
2. Falls back to recursive character splitting
3. Targets ~500 tokens per chunk with ~50 token overlap
4. Preserves all metadata from parent documents
5. Saves chunks to data/chunks/

Also create a utility to visualize chunks for quality checking.

Run on our extracted documents and verify chunks look reasonable.
```

### Phase 5 Prompt (Vector Store):
```
Let's work on Phase 5: Vector Store Setup.

Create src/rag/vectorstore.py that:
1. Uses ChromaDB with persistent storage in chroma_db/
2. Uses HuggingFace BGE embeddings (BAAI/bge-small-en-v1.5)
3. Implements: initialize_vectorstore(), add_documents(), query_similar(), get_stats()
4. Handles duplicates (skip if chunk already indexed)

Create scripts/03_build_vectorstore.py to:
1. Load all chunks from data/chunks/
2. Add them to the vector store
3. Report statistics when complete

Test with a few queries to verify retrieval works.
```

### Phase 6 Prompt (RAG Engine):
```
Let's work on Phase 6: RAG Query Engine.

Create src/rag/query_engine.py that:
1. Uses Claude Sonnet via the Anthropic API
2. Retrieves relevant chunks from our vector store
3. Constructs prompts with context and instructions
4. Returns answers with source citations
5. Handles errors gracefully

Use the system prompt from CLAUDE.md.

Create a test script that runs several test questions and shows:
- The answer
- Source citations
- Response time
```

### Phase 7 Prompt (Streamlit UI):
```
Let's work on Phase 7: Streamlit Interface.

Use the Streamlit MCP server to create src/app/streamlit_app.py with:
1. Chat interface with history
2. Sidebar with info about the tool and example questions
3. Expandable source citations for each answer
4. Loading indicators during queries
5. Clear chat button
6. Proper error handling

Follow the UI mockup in CLAUDE.md.

Test the full flow from question to answer.
```

### Phase 8 Prompt (Testing):
```
Let's work on Phase 8: Testing & Refinement.

Create tests/ with:
1. test_scraper.py - Test URL discovery and extraction
2. test_chunker.py - Test chunking logic
3. test_rag.py - Test retrieval and response quality

Also create a quality evaluation script that:
1. Runs predefined test questions
2. Checks for appropriate citations
3. Tests hallucination resistance
4. Reports metrics

Run the evaluation and identify areas for improvement.
```

---

## 💡 Tips for Working with Claude Code

1. **One phase at a time**: Complete and verify each phase before moving on

2. **Share errors completely**: If something fails, paste the full error message

3. **Use MCP servers**: Explicitly ask Claude Code to use Playwright for web scraping

4. **Check outputs**: After each step, verify the output files look correct

5. **Update CLAUDE.md**: Ask Claude Code to update the checkboxes and session notes

6. **Git commits**: Commit after each successful phase
   ```
   git add -A
   git commit -m "Complete Phase N: [description]"
   ```

7. **Ask questions**: If you don't understand something, ask Claude Code to explain

---

## Troubleshooting

### "MCP server not found"
Make sure Playwright and Streamlit MCP servers are installed and configured in VSCode settings.

### "Module not found"
Run `pip install -r requirements.txt` in your virtual environment.

### "API key error"
Ensure .env file exists with your ANTHROPIC_API_KEY.

### Granicus site structure changed
Ask Claude Code to take a fresh screenshot and re-analyze the page structure.

---

## File Checklist

Before starting, ensure you have:
- [ ] VSCode with Claude Code extension installed
- [ ] Playwright MCP server configured
- [ ] Streamlit MCP server configured  
- [ ] An Anthropic API key (from console.anthropic.com)
- [ ] Python 3.9+ installed
- [ ] The CLAUDE.md file in your project directory

Good luck with your project!
