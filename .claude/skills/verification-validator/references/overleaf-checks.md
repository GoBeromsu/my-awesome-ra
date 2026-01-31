# Overleaf-Specific Verification

Project-specific checks for the Overleaf Evidence Panel module.

## Import Path Validation

Overleaf uses specific import path patterns. Verify correct usage:

### Expected Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| `@modules/` | Module imports (no slash after @) | `@modules/evidence-panel/frontend/js/...` |
| `@/features/` | Feature imports (with slash after @) | `@/features/pdf-preview/components/...` |
| `@/shared/` | Shared imports | `@/shared/components/...` |

### Verification Command

```bash
# Check for correct import patterns
grep -r "from '@" overleaf/services/web/modules/evidence-panel/frontend/js/ | head -20

# Find incorrect patterns (should return empty)
grep -rE "from '@/modules" overleaf/services/web/modules/evidence-panel/frontend/js/
```

### Common Mistakes

```typescript
// WRONG: slash after @ for modules
import { X } from '@/modules/evidence-panel/...'

// CORRECT: no slash after @ for modules
import { X } from '@modules/evidence-panel/...'

// WRONG: no slash after @ for features
import { X } from '@features/...'

// CORRECT: slash after @ for features
import { X } from '@/features/...'
```

## CSS Variable Usage

Overleaf uses CSS custom properties for theming. Always use variables instead of hardcoded colors.

### Verification Command

```bash
# Check for CSS variable usage
grep -E "var\(--" overleaf/services/web/modules/evidence-panel/frontend/js/*.scss

# Find hardcoded colors (potential issues)
grep -E "color:\s*(#|rgb|hsl)" overleaf/services/web/modules/evidence-panel/frontend/js/*.scss
```

### Expected Patterns

```scss
// CORRECT: Using theme variables
color: var(--content-primary);
background: var(--bg-light-secondary);
border: 1px solid var(--border-divider);

// WRONG: Hardcoded colors
color: #333;
background: white;
border: 1px solid #ccc;
```

### Common Variables

| Variable | Purpose |
|----------|---------|
| `--content-primary` | Primary text color |
| `--content-secondary` | Secondary text color |
| `--bg-light-primary` | Primary background |
| `--bg-light-secondary` | Secondary background |
| `--border-divider` | Border/divider color |
| `--link-ui` | Link color |

## i18n Key Verification

All user-facing strings should use translation keys.

### Verification Command

```bash
# Extract used translation keys
grep -ohE "t\\('[^']+'\\)" overleaf/services/web/modules/evidence-panel/frontend/js/*.tsx | \
  sed "s/t('\\([^']*\\)')/\\1/" | sort -u

# Check if keys exist in en.json
for key in $(grep -ohE "t\\('[^']+'\\)" modules/evidence-panel/frontend/js/*.tsx | sed "s/t('\\([^']*\\)')/\\1/"); do
  grep -q "\"$key\"" overleaf/services/web/locales/en.json || echo "Missing: $key"
done
```

### Expected Pattern

```typescript
// CORRECT: Using translation
<span>{t('evidence_panel_title')}</span>

// WRONG: Hardcoded string
<span>Evidence Panel</span>
```

## New Editor Compatibility

If using IDE redesign features, verify compatibility with both old and new editor.

### Check for New Editor Usage

```bash
grep -r "useIsNewEditorEnabled" overleaf/services/web/modules/evidence-panel/frontend/js/
```

### Expected Pattern

```typescript
import { useIsNewEditorEnabled } from '@/features/ide-redesign/utils/new-editor-utils'

function MyComponent() {
  const isNewEditor = useIsNewEditorEnabled()

  // Handle both cases
  if (isNewEditor) {
    return <NewEditorVersion />
  }
  return <LegacyVersion />
}
```

## Docker Webpack Verification

### Quick Check

```bash
cd /Users/beomsu/Documents/My\ Awesome\ RA/overleaf/develop
docker compose logs webpack --tail 30 | grep -E "compiled|error|Error"
```

### Expected Output

```
webpack-1  | [webpack-cli] Compilation finished
webpack-1  | compiled successfully in 4.2s
```

### Restart Webpack (if needed)

```bash
docker compose restart webpack
sleep 20
docker compose logs webpack --tail 20
```

## Frontend Unit Tests

### Run Evidence Panel Tests

```bash
docker exec develop-web-1 sh -c \
  "cd /overleaf/services/web && npm run test:frontend -- --grep 'Evidence'"
```

### Expected Output

```
  Evidence Panel
    ✓ renders search input
    ✓ displays results on search
    ✓ handles empty results

  3 passing (0.5s)
```

## Verification Checklist

Before marking verification complete:

- [ ] Import paths follow Overleaf conventions
- [ ] CSS uses theme variables (no hardcoded colors)
- [ ] All strings use i18n keys
- [ ] Webpack compiles without errors
- [ ] Frontend unit tests pass
- [ ] No console errors in browser
- [ ] Visual appearance correct (screenshot)
