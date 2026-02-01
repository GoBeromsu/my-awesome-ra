# My Awesome RA

AI service for reference-grounded LaTeX paper writing. AGPL-3.0 license.

## Commands

```bash
# API server (standalone)
cd apps/api && source .venv/bin/activate && uv run uvicorn src.main:app --reload

# Backend tests
cd apps/api && pytest -v --tb=short

# Dev environment (hot reload)
cd overleaf/develop && bin/dev web webpack
# → http://localhost (Evidence Panel + live reload)

# Demo environment (production build)
cd deployment && docker compose up --build
# Wait ~2 min, then: ../scripts/setup-demo.sh
# → http://localhost (demo@example.com / Demo@2024!Secure)

# Frontend tests (inside Docker)
docker exec develop-web-1 sh -c "cd /overleaf/services/web && npm run test:frontend -- --grep 'Evidence'"

# Webpack status
docker compose -f overleaf/develop/docker-compose.yml logs webpack --tail 20 | grep -E "compiled|error"
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

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evidence/search` | Search evidence |
| POST | `/documents/parse` | Parse PDF (SOLAR API) |
| POST | `/documents/index` | Index to FAISS |
| GET | `/documents/{id}/chunks` | Get chunks |
| GET | `/health` | Health check |
