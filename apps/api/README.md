# My Awesome RA API

FastAPI backend for AI Agent service providing reference-grounded LaTeX paper writing.

## Features

- Evidence search via ChromaDB vector store
- Document parsing via Upstage SOLAR API
- Citation extraction

## Quick Start

```bash
# Install dependencies
uv sync

# Run server
uv run uvicorn src.main:app --reload
```

## Endpoints

### Core
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/evidence/search` | Search evidence by query |
| POST | `/chat/ask` | RAG Q&A with document context |

### Document Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents` | List all indexed documents |
| POST | `/documents/upload` | Upload PDF → Parse (SOLAR) → Index (ChromaDB) in background |
| GET | `/documents/{id}/status` | Check indexing status (processing/indexed/error) |
| GET | `/documents/{id}/chunks` | Get all chunks for a document |
| GET | `/documents/{id}/file` | Download original PDF |
| POST | `/documents/{id}/reindex` | Re-parse and re-index existing PDF |
| DELETE | `/documents/{id}` | Remove document from index |

### Citations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/citations/extract` | Extract structured citations from text |
