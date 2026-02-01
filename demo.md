# My Awesome RA Demo Scenario

AI-powered reference-grounded LaTeX paper writing assistant demo.

## Prerequisites

- Demo server running: `cd apps/api && uv run uvicorn src.main:app --reload`
- Overleaf dev environment: `cd overleaf/develop && bin/dev web webpack`
- Seed data loaded (see below)

---

## Seed Data (Initial State)

Demo starts with pre-seeded data. The seed ensures a consistent, reproducible demo environment.

### Seed Components

| Component | Location | Description |
|-----------|----------|-------------|
| Demo User | Overleaf DB | `demo@example.com` / `Demo@2024!Secure` |
| Demo Project | Overleaf DB | Pre-configured LaTeX project with `references.bib` |
| Source PDFs | `fixtures/papers/` | Original PDF papers |
| Cite Key Mapping | `fixtures/pdf_citekey_mapping.json` | PDF filename ↔ citeKey mapping |
| ChromaDB Index | `fixtures/seed/chroma.sqlite3` + `27eb0fa1-.../` | Vector store with embeddings and metadata |
| Renamed PDFs | `fixtures/seed/pdfs/` | Same PDFs, renamed to `{document_id}.pdf` for API serving |

### Seed Architecture

```
fixtures/
├── papers/                          # Source PDFs (original names)
│   ├── Vaswani et al. - 2017 - Attention is All you Need.pdf
│   ├── Fan et al. - 2023 - Large Language Models for SE.pdf
│   └── ...
│
├── pdf_citekey_mapping.json         # Maps filename → citeKey
│   {
│     "Vaswani et al. - 2017 - Attention is All you Need.pdf": "Vaswani2017Attention",
│     "Fan et al. - 2023 - Large Language Models for SE.pdf": "Fan2023Large"
│   }
│
└── seed/
    ├── chroma.sqlite3               # ChromaDB database
    ├── 27eb0fa1-.../                # ChromaDB index directory
    └── pdfs/                        # PDFs renamed for API serving
        ├── Vaswani2017Attention_a1b2c3d4e5f6.pdf  # 원본과 동일, 이름만 변경
        └── Fan2023Large_b2c3d4e5f6a7.pdf
```

### Document ID Format

Each PDF gets a unique document ID in the format: `{citeKey}_{sha256[:12]}`

Example:
- citeKey: `Vaswani2017Attention`
- SHA256 hash: `a1b2c3d4e5f6...`
- Document ID: `Vaswani2017Attention_a1b2c3d4e5f6`

This ensures:
- Predictable IDs linked to bibliography entries
- Collision prevention via content hash
- Pattern validation: `^[\w\-\.]+_[a-f0-9]{12}$`

### Metadata Structure

Each chunk in `metadata.npy` contains:

```python
{
    # Document identification
    "document_id": "Vaswani2017Attention_a1b2c3d4e5f6",
    "chunk_id": "Vaswani2017Attention_a1b2c3d4e5f6_0",
    "cite_key": "Vaswani2017Attention",

    # Chunk content & position
    "text": "The dominant sequence transduction models...",
    "start_idx": 0,
    "end_idx": 400,
    "page": 1,

    # Paper metadata
    "title": "Attention is All you Need",
    "year": 2017,
    "pages": 15,
    "page_count": 15,
    "source_pdf": "Vaswani et al. - 2017 - Attention is All you Need.pdf",
    "indexed_at": "2024-01-15T10:30:00Z",
}
```

### Seed Setup Commands

```bash
# 1. Reset Overleaf database with demo user/project
cd overleaf/develop && bin/seed

# 2. Copy seed ChromaDB index to API data directory
mkdir -p apps/api/data/chroma apps/api/data/pdfs
cp fixtures/seed/chroma.sqlite3 apps/api/data/chroma/
cp -r fixtures/seed/27eb0fa1-*/ apps/api/data/chroma/

# 3. Copy seed PDFs to API storage
cp fixtures/seed/pdfs/*.pdf apps/api/data/pdfs/

# 4. Verify seed data
cd apps/api && pytest tests/integration/test_search_with_seed.py -v
```

### Regenerate Seed (When PDFs Change)

```bash
# Run from project root
cd apps/api && uv run python ../../scripts/regenerate_seed.py

# This will:
# 1. Read fixtures/pdf_citekey_mapping.json for PDF ↔ citeKey mapping
# 2. Parse all PDFs in fixtures/papers/ using SOLAR API
# 3. Generate embeddings (4096-dim) using Upstage Embedding API
# 4. Build ChromaDB index (cosine similarity)
# 5. Save to fixtures/seed/ (chroma.sqlite3, index directory, pdfs/)
# 6. Validate indexed data against expected schema
```

### Playwright: Verify Seed State

```typescript
// Verify seed data is loaded
test.beforeEach(async ({ page }) => {
  // Login
  await page.goto('http://localhost:3000')
  await page.getByLabel('Email').fill('demo@example.com')
  await page.getByLabel('Password').fill('Demo@2024!Secure')
  await page.getByRole('button', { name: 'Login' }).click()

  // Verify demo project exists
  await expect(page.getByText('Demo Project')).toBeVisible()
})

test('seed data is indexed', async ({ page }) => {
  // Open References Panel
  await page.locator('[aria-label="References"]').click()
  const referencesPanel = page.locator('.references-panel')
  await expect(referencesPanel).toBeVisible()

  // Verify at least some papers are indexed
  const indexedCount = page.locator('.references-panel-count')
  await expect(indexedCount).not.toHaveText('0/')

  // Verify evidence search works
  const editor = page.locator('.cm-content')
  await editor.click()

  // Wait for evidence results
  await expect(page.locator('.evidence-list[role="list"]')).toBeVisible({ timeout: 10000 })
})
```

---

## Demo Flow

### 1. Login to Demo Project

1. Navigate to `http://localhost:3000`
2. Login with demo credentials:
   - Email: `demo@example.com`
   - Password: `Demo@2024!Secure`
3. Open demo project (e.g., "AI Survey Paper")

**Playwright Selectors:**
```typescript
await page.getByLabel('Email').fill('demo@example.com')
await page.getByLabel('Password').fill('Demo@2024!Secure')
await page.getByRole('button', { name: 'Login' }).click()
```

---

### 2. Reference Panel Overview

1. Click **References** icon in left rail (book icon)
2. Reference Library panel opens

**Expected State**: All PDFs from `references.bib` are listed:
```
├── vaswani2017 - Attention Is All You Need    [✓ Indexed]
├── brown2020 - Language Models are Few-Shot   [✓ Indexed]
├── devlin2019 - BERT: Pre-training of Deep    [✓ Indexed]
├── radford2019 - Language Models are          [○ No PDF]
└── lecun2015 - Deep Learning                  [○ No PDF]
```

**Key Point**: List is dynamically generated from `.bib` file entries.

**Playwright Selectors:**
```typescript
// References Panel
const referencesPanel = page.locator('.references-panel')
await expect(referencesPanel).toBeVisible()

// Header with count
const headerCount = page.locator('.references-panel-count')
await expect(headerCount).toHaveText(/\d+\/\d+/)  // e.g., "3/5"

// Processing indicator (spinning)
const processingIndicator = page.locator('.references-panel-processing .icon-spin')

// Reference tree
const referenceTree = page.locator('.references-tree[role="tree"]')

// Individual reference item
const referenceItem = page.locator('.reference-tree-item')
await expect(referenceItem).toHaveCount(5)

// Specific reference by citeKey
const vaswaniItem = page.locator('.reference-tree-item[aria-label="vaswani2017"]')
```

---

### 3. Upload New PDF

1. Click **Upload** button in header
2. Select PDF file
3. Observe auto-indexing progress

**Status Flow:**
```
⟳ Indexing... → ✓ Indexed (42 chunks)
```

**Playwright Selectors:**
```typescript
// Upload button in header
const uploadBtn = page.locator('[aria-label="upload_pdf_files"]')
await uploadBtn.click()

// File input (hidden)
const fileInput = page.locator('input[type="file"][accept=".pdf"]')
await fileInput.setInputFiles('/path/to/paper.pdf')

// Wait for indexing to complete
await page.waitForSelector('.status-icon--warning', { state: 'hidden' })  // spinner gone
await page.waitForSelector('.status-icon--success >> text=check_circle')  // indexed

// Verify chunk count appears (optional)
// Status icons container
const statusIcons = page.locator('.reference-status-icons')
```

---

### 4. Status Icons (UI Component Reference)

| Status | Icon | Class | Material Icon |
|--------|------|-------|---------------|
| PDF Uploaded | Green PDF | `.status-icon--success` | `picture_as_pdf` |
| No PDF | Gray PDF | `.status-icon--muted` | `picture_as_pdf` |
| Indexed | Green Check | `.status-icon--success` | `check_circle` |
| Indexing | Spinner | `.status-icon--warning` | `OLSpinner` |
| Error | Red Error | `.status-icon--danger` | `error` |
| Not Indexed | Gray Circle | `.status-icon--muted` | `radio_button_unchecked` |

**Playwright Selectors:**
```typescript
// PDF status icons
const pdfUploaded = page.locator('.status-icon--success:has(span:text("picture_as_pdf"))')
const pdfMissing = page.locator('.status-icon--muted:has(span:text("picture_as_pdf"))')

// Index status icons
const indexed = page.locator('.status-icon--success:has(span:text("check_circle"))')
const indexing = page.locator('.status-icon--warning')  // has OLSpinner
const indexError = page.locator('.status-icon--danger:has(span:text("error"))')
const notIndexed = page.locator('.status-icon--muted:has(span:text("radio_button_unchecked"))')
```

---

### 5. Action Buttons (UI Component Reference)

| State | Action | Icon | Variant |
|-------|--------|------|---------|
| No PDF | Upload PDF | `upload_file` | secondary |
| Indexed | Re-index | `refresh` | secondary |
| Indexed | Remove | `delete` | danger-ghost |
| Error | Retry | `refresh` | secondary |
| Not Indexed (has PDF) | Index | `bolt` | primary |

**Playwright Selectors:**
```typescript
// Action buttons container
const actionButtons = page.locator('.reference-actions')

// Individual action buttons
const uploadPdfBtn = page.locator('[aria-label="upload_pdf"]')
const reindexBtn = page.locator('[aria-label="reindex_document"]')
const removeBtn = page.locator('[aria-label="remove_from_index"]')
const retryBtn = page.locator('[aria-label="retry_indexing"]')
const indexBtn = page.locator('[aria-label="index_document"]')
```

---

### 6. Delete Document (Remove from Index)

1. Hover over indexed reference item
2. Click **Delete** button (trash icon)
3. Document removed from index

**Playwright Selectors:**
```typescript
// Hover over item to reveal actions
const brownItem = page.locator('.reference-tree-item[aria-label="brown2020"]')
await brownItem.hover()

// Click remove button
const removeBtn = brownItem.locator('[aria-label="remove_from_index"]')
await removeBtn.click()

// Verify item status changed (no longer indexed)
await expect(brownItem.locator('.status-icon--success:has(span:text("check_circle"))')).toBeHidden()
```

---

### 7. Re-index Document

1. Hover over indexed reference
2. Click **Re-index** button (refresh icon)
3. Observe re-indexing progress

**Playwright Selectors:**
```typescript
// Find indexed item
const vaswaniItem = page.locator('.reference-tree-item[aria-label="vaswani2017"]')

// Click reindex
const reindexBtn = vaswaniItem.locator('[aria-label="reindex_document"]')
await reindexBtn.click()

// Wait for indexing spinner
await expect(vaswaniItem.locator('.status-icon--warning')).toBeVisible()

// Wait for completion
await expect(vaswaniItem.locator('.status-icon--success:has(span:text("check_circle"))')).toBeVisible()
```

---

### 8. Evidence Search (Auto-triggered by Cursor)

**Key Feature**: Evidence panel updates **automatically** based on cursor position in the LaTeX editor. No manual search needed.

1. Click in a paragraph within the LaTeX editor
2. Evidence panel automatically searches for related references
3. Results appear sorted by similarity score

**Playwright Selectors:**
```typescript
// Evidence panel
const evidencePanel = page.locator('.evidence-panel')
const evidenceViewer = page.locator('[data-testid="evidence-viewer"]')

// Auto-toggle switch
const autoToggle = page.locator('.evidence-auto-toggle')

// Current context display
const contextLabel = page.locator('.evidence-context-label')
const contextText = page.locator('.evidence-context-text')

// Loading state
const loadingSpinner = page.locator('.evidence-loading')
const loadingText = page.locator('.evidence-loading-text')

// Results
const resultsHeader = page.locator('.evidence-results-header')
const resultsCount = page.locator('.evidence-results-count')
const evidenceList = page.locator('.evidence-list[role="list"]')

// No results state
const noResults = page.locator('.evidence-no-results')
const noResultsHint = page.locator('.evidence-no-results-hint')

// Placeholder (before search)
const placeholder = page.locator('.evidence-placeholder')
```

---

### 9. Evidence Item Details

Each evidence result shows:
- Rank and similarity score
- Paper title, authors, year
- Expandable snippet
- Page number
- Copy and View PDF buttons

**Playwright Selectors:**
```typescript
// Evidence item (using role)
const evidenceItem = page.locator('[role="listitem"].log-entry')

// Item components
const evidenceRank = page.locator('.evidence-rank')  // #1, #2, etc.
const evidenceScore = page.locator('.evidence-score')  // 92%, 78%, etc.
const evidenceHeader = page.locator('.evidence-item-header')

// Expand/collapse button
const expandBtn = page.locator('.log-entry-header-link')

// Expanded content
const evidenceSnippet = page.locator('.evidence-snippet')
const evidenceMeta = page.locator('.evidence-meta')
const metaPage = page.locator('.evidence-meta-item:has(span:text("description"))')

// Action buttons
const copyBtn = page.locator('.evidence-actions button:has-text("Copy")')
const viewPdfBtn = page.locator('.evidence-actions button:has-text("View PDF")')

// Cited vs non-cited styling
const citedItem = page.locator('.evidence-item--cited')
const nonCitedItem = page.locator('.evidence-item--non-cited')
```

---

### 10. Score-based Styling

| Score Range | Header Class | Color |
|-------------|--------------|-------|
| >= 80% | `log-entry-header-success` | Green |
| >= 60% | `log-entry-header-typesetting` | Yellow |
| < 60% | `log-entry-header-info` | Blue |

**Playwright Selectors:**
```typescript
// High relevance (green)
const highRelevance = page.locator('.log-entry-header-success.evidence-item-header')

// Medium relevance (yellow)
const mediumRelevance = page.locator('.log-entry-header-typesetting.evidence-item-header')

// Low relevance (blue)
const lowRelevance = page.locator('.log-entry-header-info.evidence-item-header')
```

---

## Complete Demo Scenario (Playwright E2E Test)

```typescript
import { test, expect } from '@playwright/test'

test('My Awesome RA Demo Flow', async ({ page }) => {
  // 1. Login
  await page.goto('http://localhost:3000')
  await page.getByLabel('Email').fill('demo@example.com')
  await page.getByLabel('Password').fill('Demo@2024!Secure')
  await page.getByRole('button', { name: 'Login' }).click()

  // 2. Open project
  await page.getByText('AI Survey Paper').click()
  await page.waitForSelector('.editor-container')

  // 3. Open References Panel
  await page.locator('[aria-label="References"]').click()
  const referencesPanel = page.locator('.references-panel')
  await expect(referencesPanel).toBeVisible()

  // 4. Verify existing references
  const headerCount = page.locator('.references-panel-count')
  await expect(headerCount).toContainText('/')

  // 5. Upload new PDF
  const uploadBtn = page.locator('[aria-label="upload_pdf_files"]')
  await uploadBtn.click()

  const fileInput = page.locator('input[type="file"][accept=".pdf"]')
  await fileInput.setInputFiles('fixtures/seed/pdfs/lecun2015.pdf')

  // 6. Wait for indexing
  await page.waitForSelector('.status-icon--warning', { timeout: 10000 })  // indexing started
  await page.waitForSelector('.status-icon--warning', { state: 'hidden', timeout: 30000 })  // indexing done

  // 7. Verify indexed
  const lecunItem = page.locator('.reference-tree-item[aria-label="lecun2015"]')
  await expect(lecunItem.locator('.status-icon--success')).toHaveCount(2)  // PDF + indexed

  // 8. Delete a reference
  const brownItem = page.locator('.reference-tree-item[aria-label="brown2020"]')
  await brownItem.hover()
  await brownItem.locator('[aria-label="remove_from_index"]').click()

  // 9. Re-index a reference
  const vaswaniItem = page.locator('.reference-tree-item[aria-label="vaswani2017"]')
  await vaswaniItem.hover()
  await vaswaniItem.locator('[aria-label="reindex_document"]').click()
  await expect(vaswaniItem.locator('.status-icon--warning')).toBeVisible()
  await expect(vaswaniItem.locator('.status-icon--success:has(span:text("check_circle"))')).toBeVisible({ timeout: 30000 })

  // 10. Click in LaTeX editor to trigger evidence search
  const editor = page.locator('.cm-content')  // CodeMirror editor
  await editor.click({ position: { x: 100, y: 200 } })  // Click in a paragraph

  // 11. Verify evidence panel updates automatically
  const evidenceViewer = page.locator('[data-testid="evidence-viewer"]')
  await expect(evidenceViewer).toBeVisible()

  // 12. Wait for evidence results
  await page.waitForSelector('.evidence-list[role="list"]', { timeout: 10000 })

  // 13. Verify results are sorted by score
  const scores = await page.locator('.evidence-score').allTextContents()
  const numericScores = scores.map(s => parseInt(s.replace('%', '')))
  expect(numericScores).toEqual([...numericScores].sort((a, b) => b - a))

  // 14. Expand first result
  const firstResult = page.locator('[role="listitem"].log-entry').first()
  await firstResult.locator('.log-entry-header').click()

  // 15. Verify expanded content
  await expect(firstResult.locator('.evidence-snippet')).toBeVisible()
  await expect(firstResult.locator('.evidence-meta')).toBeVisible()

  // 16. Click View PDF
  const [newPage] = await Promise.all([
    page.waitForEvent('popup'),
    firstResult.locator('button:has-text("View PDF")').click()
  ])
  await expect(newPage).toHaveURL(/\/documents\/.*\/file#page=\d+/)
  await newPage.close()

  console.log('Demo completed successfully!')
})
```

---

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /documents` | List all indexed documents |
| `POST /documents/upload` | Upload + auto-index PDF |
| `GET /documents/{id}/status` | Poll processing status |
| `POST /documents/{id}/reindex` | Re-parse and re-index |
| `DELETE /documents/{id}` | Remove document + chunks |
| `POST /evidence/search` | Semantic search query |
| `GET /documents/{id}/file` | Serve PDF for viewing |

---

## Demo Script (5 minutes)

1. **[0:00]** Login and open project
2. **[0:30]** Show Reference Panel with existing papers
3. **[1:00]** Upload new PDF, watch auto-indexing
4. **[1:30]** Delete a document
5. **[2:00]** Re-index existing document
6. **[2:30]** Switch to LaTeX editor
7. **[3:00]** Click in paragraph → evidence appears automatically
8. **[3:30]** Expand result, show details + PDF link
9. **[4:00]** Click View PDF, show page navigation
10. **[4:30]** Summarize: "AI-grounded citations in real-time"

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No references shown | Check `.bib` file exists in project |
| Upload fails | Verify API server is running on :8000 |
| Indexing stuck | Check SOLAR API key in `.env` |
| No evidence results | Verify ChromaDB index has documents (`data/chroma/`) |
| PDF won't open | Check `data/pdfs/` has the file |
| Evidence not updating | Check auto-toggle is enabled |
