# My Awesome RA - Demo Package

AI-powered reference-grounded LaTeX paper writing with Evidence Panel.

## What's Included

- **FastAPI Backend**: Evidence search API with SOLAR embeddings
- **Pre-indexed Data**: 29 research papers with 3,192 embeddings
- **Papers Included**: Transformer (Vaswani), LoRA (Hu), LLMs, Software Engineering

## Quick Start (API Demo)

### 1. Prerequisites

- Docker Desktop (with Docker Compose v2)
- Upstage API Key ([Get one here](https://console.upstage.ai/))

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and set your UPSTAGE_API_KEY
```

### 3. Start the API

```bash
docker compose up -d
```

### 4. Test the API

Open http://localhost:8000/docs in your browser to access the Swagger UI.

**Test evidence search:**
```bash
curl -X POST http://localhost:8000/evidence/search \
  -H "Content-Type: application/json" \
  -d '{"query": "attention mechanism transformer", "top_k": 5}'
```

**List indexed documents:**
```bash
curl http://localhost:8000/documents
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/documents` | List indexed documents |
| GET | `/documents/{id}/chunks` | Get document chunks |
| POST | `/evidence/search` | Search for relevant evidence |

## Full Demo with Evidence Panel UI

To experience the full Evidence Panel integrated into the Overleaf LaTeX editor, clone the main repository:

```bash
# Clone the repository
git clone https://github.com/your-org/my-awesome-ra.git
cd my-awesome-ra

# Initialize submodules
git submodule update --init --recursive

# Start the API
./scripts/demo.sh

# In another terminal, start Overleaf
cd overleaf/develop
bin/dev web webpack
```

Then access http://localhost:80 and log in with:
- Email: `demo@example.com`
- Password: `Demo@2024!Secure`

## Pre-indexed Papers

| Cite Key | Title | Year |
|----------|-------|------|
| Vaswani2017Attention | Attention Is All You Need | 2017 |
| Hu2021LoRA | LoRA: Low-Rank Adaptation | 2021 |
| Yang2025Qwen3 | Qwen3 Technical Report | 2025 |
| Abdin2024Phi4 | Phi-4 Technical Report | 2024 |
| ... and 25 more papers | | |

## Troubleshooting

### API not starting?

```bash
# Check logs
docker compose logs ra-api

# Verify API key
grep UPSTAGE_API_KEY .env
```

### Build failing?

```bash
# Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

## Stopping

```bash
docker compose down
```

To remove built images:
```bash
docker compose down --rmi local
```

## Architecture

```
+-------------+
|   Browser   |
+------+------+
       |
+------v------+
|  ra-api     |  FastAPI Backend
|  :8000      |  - Evidence Search
+------+------+  - Document Management
       |
+------v------+
|  ChromaDB   |  Vector Store (embedded)
|  SQLite     |  - 3,192 embeddings
+-------------+  - 29 documents
```

## License

AGPL-3.0
