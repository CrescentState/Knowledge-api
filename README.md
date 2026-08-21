# Knowledge Base API

A FastAPI prototype for asynchronous PDF document processing. Upload a PDF, get an immediate acknowledgment, and the extraction happens in the background using Docling.

> **Status:** Phase 1 prototype. Handles PDF ingestion and text extraction. Database persistence, LLM integration, and vector search are on the roadmap.

---

## What It Actually Does

- Accepts PDF uploads via `POST /api/v1/documents/upload`
- Returns `202 Accepted` immediately — no waiting for extraction
- Processes the PDF in a background task using [Docling](https://github.com/DS4SD/docling)
- Extracts content as Markdown, counts pages, and measures processing time
- Logs extraction metrics via Loguru
- Cleans up temporary files after processing
- Provides a health check at `GET /health`

**What it does NOT do yet:**

- Handle images or non-PDF files
- Integrate with LLMs or vector stores
- Provide retrieval endpoints for processed documents
- Authenticate users or rate-limit requests

---



## Tech Stack


| Layer            | Tool                         |
| ---------------- | ---------------------------- |
| Framework        | FastAPI (Python 3.12+)       |
| Document Parsing | Docling                      |
| Validation       | Pydantic + Pydantic Settings |
| Logging          | Loguru                       |
| Server           | Uvicorn                      |
| Packaging        | 0uv                          |
| Container        | Docker (multi-stage build)   |


---



## Project Structure

```
knowledge-base-api/
├── app/
│   ├── main.py              # FastAPI app, lifespan, CORS, router mount
│   ├── api/v1/router.py     # Upload endpoint + background task worker
│   ├── services/document.py # Docling wrapper: PDF → Markdown extraction
│   ├── schemas/
│   │   ├── base.py          # Shared Pydantic base model
│   │   └── document.py      # ExtractionResult schema
│   └── core/
│       ├── config.py        # Pydantic Settings (.env support)
│       └── logging.py       # Loguru configuration
├── pyproject.toml           # Dependencies (uv)
├── uv.lock                  # Reproducible lockfile
├── DockerFile               # Multi-stage build, non-root user
└── README.md                # This file
```

---



## Architecture



### Lifespan Management

The app uses FastAPI's `lifespan` context manager:

1. **Startup:** Instantiates `DocumentProcessor` (loads Docling models into memory)
2. **Runtime:** API serves requests; heavy extraction runs in background tasks
3. **Shutdown:** Clears app state

This keeps the Docling model warm across requests instead of reloading it per upload.

### Request Flow

```
Client → POST /api/v1/documents/upload (multipart/form-data)
         ↓
Server → Validates file type (PDF only)
         ↓
Server → Saves file to temp path (temp_<filename>.pdf)
         ↓
Server → Queues background task → Returns 202 Accepted immediately
         ↓
Background → Docling converts PDF → Markdown
             → Measures page count + processing time
             → Logs results via Loguru
             → Deletes temp file
```

**Important:** The client receives only an acknowledgment. To check results, you currently need to read the server logs. A database + retrieval endpoint is planned for Phase 2.

---



## API Endpoints


| Method | Path                       | Description                            |
| ------ | -------------------------- | -------------------------------------- |
| `GET`  | `/health`                  | System health + version                |
| `POST` | `/api/v1/documents/upload` | Upload a PDF for background processing |




### Upload a PDF

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@/path/to/document.pdf"
```

**Response (202 Accepted):**

```json
{
  "message": "File uploaded successfully. Processing has started in the background.",
  "filename": "document.pdf"
}
```

**Server logs (background task):**

```
2025-07-28 23:45:12 | SUCCESS  | document:process_pdf:45 - Extraction complete for document.pdf
2025-07-28 23:45:12 | INFO     | document:process_pdf:46 - Total Pages: 12
2025-07-28 23:45:12 | INFO     | document:process_pdf:47 - Total Time: 3.24s
2025-07-28 23:45:12 | INFO     | document:process_pdf:48 - Avg Time Per Page: 0.27s
```

---



## Setup



### Local Development

```bash
# 1. Clone
git clone https://github.com/CrescentState/Knowledge-base-api.git
cd Knowledge-base-api

# 2. Install dependencies (using uv)
uv sync

# 3. Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```



### Docker

```bash
# Build
docker build -f DockerFile -t knowledge-api .

# Run
docker run --rm -p 8000:8000 --name knowledge-api knowledge-api
```



### Environment Variables

Create a `.env` file (optional — app starts without it):

```env
DEBUG=False
PROJECT_NAME=Knowledge API
VERSION=0.1.0
OPENAI_API_KEY=          
DATABASE_API=                 # Reserved for Phase 2; unused currently
```

---



## Design Decisions


| Decision                       | Rationale                                                                              |
| ------------------------------ | -------------------------------------------------------------------------------------- |
| **FastAPI + async**            | Native async support; clean dependency injection                                       |
| **BackgroundTasks**            | Docling extraction is CPU-heavy; we return 202 immediately so the client isn't blocked |
| **Docling over PyPDF2**        | Docling preserves document structure (tables, sections) and exports clean Markdown     |
| **Pydantic Settings**          | Type-safe config with `.env` loading; fail-fast on missing required values             |
| **Multi-stage Docker**         | Smaller final image; separates dependency install from runtime                         |
| **Non-root user in container** | Security baseline for any deployed service                                             |
| **Loguru over stdlib logging** | Structured, colorized logs out of the box; simpler configuration                       |


---



## Roadmap

- [x] **Phase 1:** PDF upload → background extraction → logging
- [x] **Phase 2:** Persist extraction results (SQLite/PostgreSQL); add retrieval endpoints
- [ ] **Phase 3:** LLM integration (OpenAI) for document summarization and Q&A
- [ ] **Phase 4:** Vector embeddings + semantic search over processed documents
- [ ] **Phase 5:** Multi-format support (images, Word docs, scanned PDFs with OCR)

---



## License

MIT — free to use, modify, and build upon.
