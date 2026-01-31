#!/bin/bash
# Build seed data incrementally via API
# Usage: ./scripts/build_seed_via_api.sh [--dry-run]
#
# Prerequisites:
# 1. API server running: cd apps/api && uvicorn src.main:app --reload
# 2. fixtures/pdf_citekey_mapping.json exists

set -e

API_URL="${API_URL:-http://localhost:8000}"
MAPPING_FILE="fixtures/pdf_citekey_mapping.json"
PAPERS_DIR="fixtures/papers"
DRY_RUN=false
MAX_RETRIES=3
INTER_DOC_SLEEP=3  # Sleep between documents for memory release

if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN MODE ==="
fi

# Check prerequisites
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "ERROR: API server not running at $API_URL"
    echo "Start it with: cd apps/api && uvicorn src.main:app --reload"
    exit 1
fi

if [[ ! -f "$MAPPING_FILE" ]]; then
    echo "ERROR: Mapping file not found: $MAPPING_FILE"
    exit 1
fi

echo "=== Building Seed via API ==="
echo "API: $API_URL"
echo ""

# Parse mapping and upload each PDF
total=$(jq 'to_entries | map(select(.value != null)) | length' "$MAPPING_FILE")
current=0
success=0
failed=0
skipped=0

for row in $(jq -r 'to_entries | map(select(.value != null)) | .[] | @base64' "$MAPPING_FILE"); do
    _jq() {
        echo ${row} | base64 --decode | jq -r ${1}
    }

    pdf_filename=$(_jq '.key')
    cite_key=$(_jq '.value')
    pdf_path="$PAPERS_DIR/$pdf_filename"

    current=$((current + 1))

    if [[ ! -f "$pdf_path" ]]; then
        echo "[$current/$total] SKIP: $cite_key (file not found)"
        skipped=$((skipped + 1))
        continue
    fi

    size_kb=$(( $(stat -f%z "$pdf_path" 2>/dev/null || stat -c%s "$pdf_path" 2>/dev/null) / 1024 ))
    echo "[$current/$total] $cite_key (${size_kb}KB)"

    if $DRY_RUN; then
        echo "  Would upload: $pdf_filename"
        continue
    fi

    # Upload with cite_key (with retry logic)
    retry_count=0
    upload_success=false

    while [[ $retry_count -lt $MAX_RETRIES ]] && [[ "$upload_success" == "false" ]]; do
        response=$(curl -s -X POST "$API_URL/documents/upload" \
            -F "file=@$pdf_path" \
            -F "cite_key=$cite_key" \
            2>&1)

        doc_id=$(echo "$response" | jq -r '.document_id // empty')
        status=$(echo "$response" | jq -r '.status // empty')

        if [[ -n "$doc_id" ]]; then
            upload_success=true
        else
            retry_count=$((retry_count + 1))
            if [[ $retry_count -lt $MAX_RETRIES ]]; then
                echo "  Retry $retry_count/$MAX_RETRIES after error: $response"
                sleep 5
            fi
        fi
    done

    if [[ "$upload_success" == "false" ]]; then
        echo "  ERROR after $MAX_RETRIES retries: $response"
        failed=$((failed + 1))
        continue
    fi

    echo "  ID: $doc_id"
    echo "  Status: $status"

    # Poll for completion (max 5 minutes per document)
    if [[ "$status" == "processing" ]]; then
        echo "  Waiting for indexing..."
        for i in {1..150}; do
            sleep 2
            poll=$(curl -s "$API_URL/documents/$doc_id/status")
            poll_status=$(echo "$poll" | jq -r '.status // empty')

            if [[ "$poll_status" == "indexed" ]]; then
                chunks=$(echo "$poll" | jq -r '.chunk_count // 0')
                echo "  Done: $chunks chunks"
                success=$((success + 1))
                break
            elif [[ "$poll_status" == "error" ]]; then
                msg=$(echo "$poll" | jq -r '.message // "unknown"')
                echo "  ERROR: $msg"
                failed=$((failed + 1))
                break
            fi

            # Progress indicator every 10 polls
            if (( i % 10 == 0 )); then
                echo "  Still processing... (${i}0s)"
            fi
        done
    elif [[ "$status" == "indexed" ]]; then
        success=$((success + 1))
    fi

    echo ""

    # Sleep between documents to allow memory release
    if [[ $current -lt $total ]]; then
        echo "  Waiting ${INTER_DOC_SLEEP}s before next document..."
        sleep $INTER_DOC_SLEEP
    fi
done

echo "=== Summary ==="
echo "Success: $success"
echo "Failed: $failed"
echo "Skipped: $skipped"
echo "Total: $total"

if [[ $success -gt 0 ]]; then
    echo ""
    echo "To save as seed data:"
    echo "  cp data/faiss/index.faiss fixtures/seed/"
    echo "  cp data/faiss/metadata.npy fixtures/seed/"
    echo "  cp data/pdfs/*.pdf fixtures/seed/pdfs/"
fi
