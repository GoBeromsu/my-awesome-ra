# My Awesome RA

> **AI Agent for Reference-Grounded LaTeX Paper Writing**
> Powered by [Upstage SOLAR API](https://console.upstage.ai/)

논문 작성 시 현재 문단에 맞는 참고문헌 근거를 자동으로 찾아주는 Evidence Panel을 Overleaf CE에 통합한 프로젝트입니다.

## Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Evidence Search** | 현재 문단 기반 관련 근거 자동 검색 | ✅ API 완료 |
| **Document Parse** | PDF → 텍스트 추출 (SOLAR Document Parse) | ✅ API 완료 |
| **Vector Index** | FAISS 기반 시맨틱 검색 | ✅ 완료 |
| **Evidence Panel UI** | Overleaf 우측 패널 | ✅ 코드 완료 |
| **Paragraph Detection** | CodeMirror 커서 위치 추적 | ✅ 코드 완료 |
| **Overleaf Integration** | 커스텀 Overleaf 빌드 | 🔄 진행 중 |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Overleaf CE                          │
│  ┌──────────────────┐    ┌────────────────────────────┐    │
│  │   LaTeX Editor   │    │     Evidence Panel         │    │
│  │  (CodeMirror)    │───▶│  - Auto/Manual Search      │    │
│  │                  │    │  - Results Display         │    │
│  └──────────────────┘    └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   /evidence  │  │  /documents  │  │  /citations  │      │
│  │    /search   │  │    /parse    │  │   /extract   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Upstage SOLAR API                      │   │
│  │  • Embedding (solar-embedding-1-large-query)        │   │
│  │  • Document Parse                                   │   │
│  │  • Information Extraction                           │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │ FAISS Index  │  (Vector Store)                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## Upstage SOLAR API 활용

### 1. Embedding API
```python
# 문단/청크 임베딩 생성
embedding = await embedding_service.embed_query("The transformer architecture...")
# → 4096차원 벡터 반환
```

### 2. Document Parse API
```python
# PDF에서 텍스트 추출
result = await solar_service.parse_document(pdf_bytes, "paper.pdf")
# → {"pages": 10, "content": "...", "metadata": {...}}
```

### 3. Information Extraction API
```python
# 인용 정보 추출
citations = await solar_service.extract_information(text, "citation")
# → {"title": "...", "authors": [...], "year": 2024}
```

## Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- Docker & Docker Compose
- [Upstage API Key](https://console.upstage.ai/)

### 1. Setup

```bash
# Clone
git clone --recursive https://github.com/GoBeromsu/my-awesome-ra.git
cd my-awesome-ra

# Environment
cp .env.example .env
# .env 파일에 UPSTAGE_API_KEY 설정

# Install dependencies
cd apps/api && uv sync
```

### 2. Run API Server

```bash
./scripts/dev.sh
# → http://localhost:8000
```

### 3. Test API

```bash
# Health check
curl http://localhost:8000/health

# PDF 파싱
curl -X POST http://localhost:8000/documents/parse \
  -F "file=@paper.pdf"

# 문서 인덱싱
curl -X POST http://localhost:8000/documents/index \
  -H "Content-Type: application/json" \
  -d '{"document_id": "paper1", "content": "...", "metadata": {"title": "..."}}'

# Evidence 검색
curl -X POST http://localhost:8000/evidence/search \
  -H "Content-Type: application/json" \
  -d '{"query": "attention mechanism in transformers"}'
```

## Project Structure

```
my-awesome-ra/
├── apps/
│   └── api/                    # FastAPI Backend
│       ├── src/
│       │   ├── main.py         # App entry
│       │   ├── routers/        # API endpoints
│       │   ├── services/       # Business logic
│       │   │   ├── embedding.py    # SOLAR Embedding
│       │   │   ├── index.py        # FAISS Index
│       │   │   └── solar.py        # SOLAR APIs
│       │   └── models/         # Pydantic models
│       └── pyproject.toml
│
├── overleaf/                   # Forked Overleaf CE (submodule)
│   └── services/web/modules/
│       └── evidence-panel/     # Evidence Panel Module
│           ├── frontend/js/
│           │   ├── components/     # React UI
│           │   ├── context/        # State management
│           │   └── hooks/          # Custom hooks
│           └── index.mjs
│
├── deployment/
│   └── docker-compose.*.yml    # Docker configs
│
└── data/                       # Local data (gitignored)
    └── faiss/                  # Vector index
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/evidence/search` | Search evidence by query |
| `POST` | `/documents/parse` | Parse PDF (SOLAR) |
| `POST` | `/documents/index` | Index document to FAISS |
| `GET` | `/documents/{id}/chunks` | Get document chunks |
| `POST` | `/citations/extract` | Extract citation info |

## Development Status

### ✅ Completed
- [x] FastAPI backend with SOLAR API integration
- [x] FAISS vector index for semantic search
- [x] Evidence Panel React components
- [x] CodeMirror paragraph detection extension
- [x] Dependency injection & proper error handling

### 🔄 In Progress
- [ ] Custom Overleaf Docker build with Evidence Panel
- [ ] E2E integration testing

### 📋 TODO
- [ ] PDF upload UI in Overleaf
- [ ] BibTeX parsing for citation metadata
- [ ] Caching for repeated searches

## Tech Stack

| Layer | Technology |
|-------|------------|
| **AI/ML** | Upstage SOLAR (Embedding, Document Parse, IE) |
| **Backend** | FastAPI, FAISS, Python 3.11 |
| **Frontend** | React, TypeScript, CodeMirror 6 |
| **Editor** | Overleaf Community Edition |
| **Infra** | Docker, uv |

## License

AGPL-3.0 (Overleaf CE 호환)

---

**Upstage AI 2기 홍보대사** | [GoBeromsu](https://github.com/GoBeromsu)
