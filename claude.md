# My Awesome RA

AI service for reference-grounded LaTeX paper writing. AGPL-3.0 license.

## Commands

```bash
# API server (standalone) - requires .env with UPSTAGE_API_KEY
cd apps/api && source .venv/bin/activate && \
  set -a && source ../../.env && set +a && \
  uv run uvicorn src.main:app --reload --port 8000

# Backend tests
cd apps/api && pytest -v --tb=short

# Dev environment (hot reload) - Full stack with all services
# First time: build CLSI with TexLive (takes ~2 min)
cd overleaf && docker build -f develop/Dockerfile.clsi-dev -t develop-clsi .
# Start all services
cd overleaf/develop && docker compose up -d mongo redis web webpack clsi filestore docstore document-updater history-v1 real-time
# Initialize MongoDB replica set (first time only):
docker exec develop-mongo-1 mongosh --quiet --eval "rs.initiate()"
# Setup demo user and project:
CONTAINER_NAME=develop-web-1 ./scripts/setup-demo.sh
# → http://localhost (Evidence Panel + live reload + PDF compile)

# Demo environment (production build)
cd deployment && docker compose up --build
# Wait ~2 min, then: ./scripts/setup-demo.sh
# → http://localhost (demo@example.com / Demo@2024!Secure)

# IMPORTANT: After modifying Dockerfile-base, rebuild in this order:
# 1. Base image (contains TexLive packages)
docker build -f overleaf/server-ce/Dockerfile-base -t sharelatex/sharelatex-base:latest overleaf/server-ce/
# 2. Main image (uses base image)
cd deployment && docker compose build --no-cache overleaf-web
# 3. Restart containers
docker compose up -d && ./scripts/setup-demo.sh

# Frontend tests (inside Docker)
docker exec develop-web-1 sh -c "cd /overleaf/services/web && npm run test:frontend -- --grep 'Evidence'"

# Webpack status
cd overleaf/develop && docker compose logs webpack --tail 20 | grep -E "compiled|error"

# Stop dev environment
cd overleaf/develop && docker compose down

# Stop demo environment
cd deployment && docker compose down
```

## Credentials

- Demo login: `demo@example.com` / `Demo@2024!Secure`

## Project Structure

```
my-awesome-ra/
├── apps/api/                    # FastAPI backend (uv, pytest)
│   ├── src/main.py              # Entry point
│   ├── src/routers/             # API endpoints
│   ├── src/services/            # Business logic
│   └── tests/
├── overleaf/                    # Overleaf CE fork (modified for Evidence Panel)
├── deployment/                  # Docker compose files
├── fixtures/                    # Demo data (seed, latex templates)
└── .claude/                     # Agents, skills, rules
```

## Overleaf Structure (Inside Docker)

```
/overleaf/services/web/
├── modules/
│   └── evidence-panel/              # OUR MODULE - only modify here
│       ├── frontend/js/             # React components
│       │   ├── components/          # UI components (panels, buttons)
│       │   ├── hooks/               # Custom React hooks
│       │   ├── contexts/            # React context providers
│       │   └── utils/               # Helper functions
│       ├── test/frontend/js/        # Mocha/Sinon frontend tests
│       └── index.mjs                # Module registration & routes
│
├── frontend/js/
│   ├── features/                    # @/features - Feature modules
│   │   ├── ide-redesign/            # New editor UI components
│   │   ├── pdf-preview/             # PDF viewer components
│   │   ├── source-editor/           # CodeMirror editor
│   │   └── outline/                 # Document outline panel
│   ├── shared/                      # @/shared - Shared utilities
│   │   ├── components/              # Reusable UI components
│   │   ├── hooks/                   # Shared React hooks
│   │   └── context/                 # Global contexts
│   └── ide/                         # Legacy IDE components
│
├── stylesheets/                     # Global SCSS styles
│   └── app/                         # App-wide styles & variables
│
└── locales/
    └── en.json                      # i18n translation keys
```

## Critical Rules

### Verification: ALWAYS use `project-verifier` agent
After ANY code change, delegate to `project-verifier` agent. It auto-selects optimal strategy:
- Backend only → pytest (~500 tokens)
- Frontend logic → webpack + tests (~2,000 tokens)
- CSS/UI → webpack + screenshot (~4,000 tokens)
- Full flow → Playwright (~10,000 tokens)

NEVER run Playwright manually for every change.

### Overleaf: Docker-only
- NEVER run `npm install` on host machine
- ALL npm operations via `docker exec`
- Only modify: `services/web/modules/evidence-panel/`

### Import paths (Overleaf-specific)
```typescript
// Module: @modules (NO slash)
import { X } from '@modules/evidence-panel/frontend/js/...'

// Feature: @/features (WITH slash)
import { X } from '@/features/pdf-preview/...'

// Shared: @/shared
import { X } from '@/shared/...'
```

### CSS: Use variables only
```scss
// CORRECT
color: var(--content-primary);

// WRONG - will break theming
color: #333;
```

## Gotchas

- Webpack success ≠ working UI. Check browser console for runtime errors.
- Frontend verification loop: Webpack → Console → Visual (in order)
- **Docker image layering**: `overleaf-web` depends on `sharelatex-base`. If you modify `Dockerfile-base`, you MUST rebuild base first, then main image. Otherwise the old base image is used.
- **Verify package installation**: After base image rebuild, check with `docker run --rm sharelatex/sharelatex-base:latest kpsewhich <package>.sty`
- **Dev CLSI with TexLive**: Dev environment uses custom `Dockerfile.clsi-dev` with TexLive installed directly (non-sandboxed). Must build the image first: `docker build -f develop/Dockerfile.clsi-dev -t develop-clsi .`

## API Endpoints

### Core Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/evidence/search` | Search evidence by query (embeddings + vector similarity) |
| POST | `/chat/ask` | RAG Q&A with document context |

### Document Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents` | List all indexed documents with metadata |
| POST | `/documents/upload` | Upload PDF → SOLAR Parse → ChromaDB indexing (background) |
| GET | `/documents/{id}/status` | Check indexing status (processing/indexed/error) |
| GET | `/documents/{id}/chunks` | Get all chunks for a document |
| GET | `/documents/{id}/file` | Download original PDF (supports #page=N) |
| POST | `/documents/{id}/reindex` | Re-parse and re-index existing PDF |
| DELETE | `/documents/{id}` | Remove document from index and delete PDF |

### Citations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/citations/extract` | Extract structured citations from text (SOLAR Information Extraction API) |
