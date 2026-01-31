# Verification Strategies

Detailed decision matrix and verification commands for each change type.

## Decision Matrix

| Signal | Strategy | Token Cost |
|--------|----------|------------|
| Only `apps/api/**` changed | pytest only | ~500 |
| Only `*.tsx` (no visual) | webpack + unit tests | ~2,000 |
| `*.scss` or visual props | webpack + screenshot | ~4,000 |
| `**/en.json` changed | webpack + snapshot | ~3,000 |
| Multiple components | full Playwright | ~10,000 |

## Backend (FastAPI)

### When to Use
- Files in `apps/api/**` changed
- No frontend files modified

### Verification Steps

```bash
# Navigate to API directory
cd /Users/beomsu/Documents/My\ Awesome\ RA/apps/api

# Activate virtual environment and run tests
source .venv/bin/activate && pytest -v --tb=short

# For specific test file
pytest tests/test_evidence.py -v

# With coverage
pytest --cov=src --cov-report=term-missing
```

### Expected Output
- All tests pass
- No import errors
- Coverage > 80%

## Frontend Logic (React Components)

### When to Use
- `*.tsx` files changed
- No `*.scss` or styling changes
- No user flow changes

### Verification Steps

```bash
# 1. Check webpack compilation
cd /Users/beomsu/Documents/My\ Awesome\ RA/overleaf/develop
docker compose logs webpack --tail 30 | grep -E "compiled|error"

# Expected: "compiled successfully"

# 2. Run frontend unit tests
docker exec develop-web-1 sh -c \
  "cd /overleaf/services/web && npm run test:frontend -- --grep 'Evidence'"

# Expected: All tests pass
```

### What to Check
- Webpack compiles without errors
- Unit tests pass
- No TypeScript errors

## Styling Changes (CSS/SCSS)

### When to Use
- `*.scss` files changed
- CSS-in-JSX style changes
- Visual props (className, style) modified

### Verification Steps

```bash
# 1. Webpack compilation
docker compose logs webpack --tail 20 | grep -E "compiled|error"

# 2. Console check via Playwright (minimal)
browser_navigate → http://localhost/login
browser_fill_form → credentials
browser_click → login
browser_console_messages → check for errors

# 3. Screenshot (targeted)
browser_take_screenshot → verify visual appearance
```

### What to Check
- Webpack compiles CSS without errors
- No console errors
- Visual appearance matches expectations

## i18n Changes (Translation Keys)

### When to Use
- `**/en.json` or other locale files changed
- `t('key')` patterns added/modified in TSX

### Verification Steps

```bash
# 1. Verify keys exist in en.json
grep -o "t('[^']*')" modules/evidence-panel/frontend/js/*.tsx | \
  sed "s/.*t('\\([^']*\\)').*/\\1/" | \
  while read key; do
    grep -q "\"$key\"" services/web/locales/en.json || echo "Missing: $key"
  done

# 2. Webpack compilation
docker compose logs webpack --tail 20 | grep -E "compiled|error"

# 3. Snapshot to verify text renders
browser_snapshot → verify translated text appears
```

## Full User Flow

### When to Use
- Multiple components changed
- User interaction patterns modified
- Critical path changes (login, save, submit)

### Verification Steps

See [playwright-patterns.md](playwright-patterns.md) for full Playwright sequence.

### What to Check
- Complete flow works end-to-end
- No console errors
- UI renders correctly
- State changes properly
