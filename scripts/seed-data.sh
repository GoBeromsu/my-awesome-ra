#!/bin/bash
#
# Seed demo data for development/testing
#
# Usage:
#   ./scripts/seed-data.sh           # Index PDFs from fixtures/papers/
#   ./scripts/seed-data.sh --copy    # Only copy pre-built index (no API calls)
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

FIXTURES_DIR="$PROJECT_DIR/fixtures"
DATA_DIR="$PROJECT_DIR/data"
SEED_DIR="$FIXTURES_DIR/seed"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "  My Awesome RA - Data Seeding"
echo "=================================="
echo

# Ensure data directories exist
mkdir -p "$DATA_DIR/faiss"
mkdir -p "$DATA_DIR/parsed"

# Load environment
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Option: --copy only copies pre-built index
if [ "$1" == "--copy" ]; then
    echo -e "${YELLOW}Mode: Copy pre-built index${NC}"
    echo

    if [ -f "$SEED_DIR/index.faiss" ] && [ -f "$SEED_DIR/metadata.npy" ]; then
        cp "$SEED_DIR/index.faiss" "$DATA_DIR/faiss/"
        cp "$SEED_DIR/metadata.npy" "$DATA_DIR/faiss/"
        echo -e "${GREEN}Successfully copied pre-built index to $DATA_DIR/faiss/${NC}"
    else
        echo -e "${RED}Error: No pre-built index found in $SEED_DIR${NC}"
        echo "Run without --copy flag to build index from PDFs"
        exit 1
    fi
    exit 0
fi

# Default: Index PDFs
echo -e "${YELLOW}Mode: Index PDFs from fixtures${NC}"
echo

# Check for PDF files
PDF_COUNT=$(find "$FIXTURES_DIR/papers" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')

if [ "$PDF_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}No PDF files found in $FIXTURES_DIR/papers/${NC}"
    echo
    echo "To use this script:"
    echo "  1. Add PDF files to fixtures/papers/"
    echo "  2. Run this script again"
    echo
    echo "Example PDFs to add:"
    echo "  - attention.pdf (Attention Is All You Need)"
    echo "  - bert.pdf (BERT paper)"
    exit 0
fi

echo "Found $PDF_COUNT PDF file(s) to index"
echo

# Check for UPSTAGE_API_KEY
if [ -z "$UPSTAGE_API_KEY" ]; then
    echo -e "${RED}Error: UPSTAGE_API_KEY not set${NC}"
    echo "Set it in .env file or export before running"
    exit 1
fi

# Run indexing script
cd "$PROJECT_DIR/apps/api"
uv run python "$SCRIPT_DIR/index_fixtures.py"

echo
echo -e "${GREEN}Data seeding complete!${NC}"
echo
echo "Next steps:"
echo "  1. Start the API server: ./scripts/dev.sh"
echo "  2. Test search: curl http://localhost:8000/evidence/search -d '{\"query\":\"attention\"}'"
