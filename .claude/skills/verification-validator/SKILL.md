---
name: verification-validator
description: Smart verification strategies for My Awesome RA. Determines optimal verification approach based on change type. Covers Backend (FastAPI/pytest) and Frontend (Overleaf/Playwright). Use with project-verifier agent or invoke directly after code changes.
---

# Verification Validator

Smart verification skill that minimizes token usage by selecting the optimal verification strategy based on change type.

## Quick Reference

| Change Type | Verification Steps | Token Cost |
|-------------|-------------------|------------|
| Backend API | `pytest` only | ~500 |
| React logic | Webpack → Unit tests | ~2,000 |
| CSS/styling | Webpack → Console → Screenshot | ~4,000 |
| i18n keys | Webpack → Snapshot | ~3,000 |
| User flow | Full Playwright sequence | ~10,000 |

## Workflow Integration

```
[Code Change]
     │
     ▼
project-verifier (orchestrator)
     │
     ├──► [1] Change Analysis (git diff)
     │
     ├──► [2] AUTO: /code-review
     │
     ├──► [3] AUTO: code-simplifier (if 50+ new lines)
     │
     ├──► [4] AUTO: /tdd (if logic change without tests)
     │
     ├──► [5] verification-validator (this skill)
     │         │
     │         ├─ Backend? → pytest
     │         ├─ Frontend logic? → webpack + unit tests
     │         ├─ Styling? → webpack + screenshot
     │         └─ User flow? → full Playwright
     │
     └──► [6] Combined Report
```

## Change Detection

```bash
# Detect change type
git diff --name-only HEAD~1 | while read file; do
  case "$file" in
    apps/api/*) echo "backend" ;;
    *.tsx)      echo "frontend-logic" ;;
    *.scss)     echo "styling" ;;
    */en.json)  echo "i18n" ;;
  esac
done | sort -u
```

## Detailed Strategies

See references:
- **Strategy selection**: [references/verification-strategies.md](references/verification-strategies.md)
- **Playwright patterns**: [references/playwright-patterns.md](references/playwright-patterns.md)
- **Overleaf checks**: [references/overleaf-checks.md](references/overleaf-checks.md)

## Token Optimization Tips

1. **Skip Playwright** for backend-only changes
2. **Screenshot first** before snapshot (smaller payload)
3. **Element snapshots** instead of full page
4. **Batch operations** in single browser session
5. **Check console without visual** for runtime error detection

## Expected Savings

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| Backend only | 12,000 | 800 | 93% |
| Frontend logic | 12,000 | 3,000 | 75% |
| Styling change | 12,000 | 5,000 | 58% |
| Full user flow | 12,000 | 12,000 | 0% |

**Average savings**: ~60-70% token reduction
