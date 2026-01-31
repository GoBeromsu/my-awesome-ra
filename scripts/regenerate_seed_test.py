#!/usr/bin/env python3
"""
Test seed regeneration with a small subset of PDFs.

Usage:
    cd apps/api && uv run python ../../scripts/regenerate_seed_test.py
"""

import asyncio
import gc
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Add the api src to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
api_src = project_root / "apps" / "api"
sys.path.insert(0, str(api_src))

# Load .env file from project root
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import faiss
import numpy as np
from numpy.typing import NDArray

from src.services.embedding import EmbeddingService
from src.services.solar import SolarService


# Configuration - reduced for testing
EMBEDDING_BATCH_SIZE = 5
MAX_CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
DIMENSION = 4096
MAX_PDF_SIZE_KB = 500  # Skip PDFs larger than 500KB for test


def chunk_text(text: str) -> list[dict]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_SIZE, len(text))
        if end < len(text):
            for sep in [". ", ".\n", "\n\n", "\n"]:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start:
                    end = last_sep + len(sep)
                    break
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({"text": chunk_text, "start_idx": start, "end_idx": end})
        start = end - CHUNK_OVERLAP if end < len(text) else len(text)
    return chunks


async def embed_in_batches(texts: list[str], embedding_service: EmbeddingService) -> list:
    """Embed texts in small batches."""
    all_embeddings = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        embeddings = await embedding_service.embed_documents(batch)
        all_embeddings.extend(embeddings)
        gc.collect()
    return all_embeddings


def generate_document_id(cite_key: str, content: bytes) -> str:
    r"""Generate document ID in citeKey_hash format."""
    file_hash = hashlib.sha256(content).hexdigest()[:12]
    safe_key = re.sub(r"[^\w\-\.]", "_", cite_key)
    safe_key = re.sub(r"_+", "_", safe_key).strip("_")
    return f"{safe_key}_{file_hash}"


def parse_year_from_filename(filename: str) -> int | None:
    """Extract year from filename."""
    match = re.search(r"[\s\-]+(\d{4})[\s\-]+", filename)
    if match:
        year = int(match.group(1))
        if 1900 <= year <= 2100:
            return year
    return None


async def process_single_pdf(
    pdf_path: Path,
    cite_key: str,
    solar_service: SolarService,
    embedding_service: EmbeddingService,
    index: faiss.IndexFlatIP,
    metadata_list: list[dict],
    pdf_storage_path: Path,
) -> dict:
    """Process a single PDF."""
    print(f"  Reading PDF...", flush=True)
    with open(pdf_path, "rb") as f:
        content = f.read()

    document_id = generate_document_id(cite_key, content)
    print(f"  [ID] {document_id}", flush=True)

    # Copy PDF
    pdf_storage_path.mkdir(parents=True, exist_ok=True)
    target_pdf = pdf_storage_path / f"{document_id}.pdf"
    if not target_pdf.exists():
        shutil.copy(pdf_path, target_pdf)

    # Parse
    print(f"  [PARSE] Calling SOLAR API...", flush=True)
    parsed = await solar_service.parse_document(content, pdf_path.name)
    del content
    gc.collect()

    text_content = parsed.get("content", "")
    if not text_content.strip():
        return {"document_id": document_id, "status": "empty", "chunk_count": 0}

    pages = parsed.get("pages", 1)
    year = parse_year_from_filename(pdf_path.name)

    # Chunk
    chunks = chunk_text(text_content)
    print(f"  [EMBED] {len(chunks)} chunks...", flush=True)

    # Embed
    texts = [c["text"] for c in chunks]
    embeddings = await embed_in_batches(texts, embedding_service)

    # Add to index
    indexed_at = datetime.now(timezone.utc).isoformat()
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = f"{document_id}_{i}"
        normalized = embedding / np.linalg.norm(embedding)
        index.add(normalized.reshape(1, -1))

        # Estimate page
        total_chars = len(text_content) if text_content else 1
        if pages > 1 and total_chars > 0:
            chunk_mid = (chunk["start_idx"] + chunk["end_idx"]) / 2
            page = min(int(chunk_mid / total_chars * pages) + 1, pages)
        else:
            page = 1

        metadata_list.append({
            "document_id": document_id,
            "chunk_id": chunk_id,
            "cite_key": cite_key,
            "text": chunk["text"],
            "start_idx": chunk["start_idx"],
            "end_idx": chunk["end_idx"],
            "page": page,
            "title": pdf_path.stem,
            "year": year,
            "pages": pages,
            "page_count": pages,
            "source_pdf": pdf_path.name,
            "indexed_at": indexed_at,
        })

    gc.collect()
    chunk_count = sum(1 for m in metadata_list if m["document_id"] == document_id)
    print(f"  [DONE] {chunk_count} chunks, {pages} pages", flush=True)

    return {"document_id": document_id, "status": "indexed", "chunk_count": chunk_count}


async def main():
    """Test seed regeneration with small PDFs."""
    fixtures_dir = project_root / "fixtures" / "papers"
    mapping_file = project_root / "fixtures" / "pdf_citekey_mapping.json"
    seed_dir = project_root / "fixtures" / "seed"
    seed_pdfs_dir = seed_dir / "pdfs"
    data_dir = project_root / "data" / "faiss"

    # Load mapping
    with open(mapping_file) as f:
        mapping = json.load(f)
    mapping = {k: v for k, v in mapping.items() if v is not None}

    if not os.getenv("UPSTAGE_API_KEY"):
        print("Error: UPSTAGE_API_KEY not set")
        sys.exit(1)

    # Find small PDFs (< 500KB)
    small_pdfs = []
    for pdf_filename, cite_key in mapping.items():
        pdf_path = fixtures_dir / pdf_filename
        if pdf_path.exists():
            size_kb = pdf_path.stat().st_size / 1024
            if size_kb < MAX_PDF_SIZE_KB:
                small_pdfs.append((pdf_path, cite_key, size_kb))

    small_pdfs.sort(key=lambda x: x[2])  # Sort by size
    small_pdfs = small_pdfs[:5]  # Take 5 smallest

    print(f"Testing with {len(small_pdfs)} small PDFs (< {MAX_PDF_SIZE_KB}KB)")
    for path, key, size in small_pdfs:
        print(f"  - {key}: {size:.1f}KB")

    # Clear seed data
    print("\nClearing seed data...")
    if seed_dir.exists():
        for f in seed_dir.glob("*"):
            if f.is_file():
                f.unlink()
        if seed_pdfs_dir.exists():
            shutil.rmtree(seed_pdfs_dir)
    seed_dir.mkdir(parents=True, exist_ok=True)
    seed_pdfs_dir.mkdir(parents=True, exist_ok=True)

    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize
    embedding_service = EmbeddingService()
    solar_service = SolarService()
    index = faiss.IndexFlatIP(DIMENSION)
    metadata_list: list[dict] = []

    results = []
    try:
        for i, (pdf_path, cite_key, size_kb) in enumerate(small_pdfs, 1):
            print(f"\n[{i}/{len(small_pdfs)}] {cite_key} ({size_kb:.1f}KB)", flush=True)
            try:
                result = await process_single_pdf(
                    pdf_path, cite_key, solar_service, embedding_service,
                    index, metadata_list, seed_pdfs_dir,
                )
                results.append(result)
            except Exception as e:
                print(f"  [ERROR] {e}", flush=True)
                results.append({"document_id": cite_key, "status": "error"})

        # Save
        print("\nSaving seed data...", flush=True)
        faiss.write_index(index, str(seed_dir / "index.faiss"))
        np.save(str(seed_dir / "metadata.npy"), np.array(metadata_list, dtype=object))

        # Summary
        print("\n" + "=" * 50)
        indexed = sum(1 for r in results if r.get("status") == "indexed")
        print(f"Indexed: {indexed}/{len(small_pdfs)}")
        print(f"Total chunks: {len(metadata_list)}")
        print(f"Seed saved to: {seed_dir}")

        # Validate document IDs
        print("\nValidating document IDs...")
        pattern = re.compile(r"^[\w\-\.]+_[a-f0-9]{12}$")
        for doc_id in set(m["document_id"] for m in metadata_list):
            if pattern.match(doc_id):
                print(f"  OK: {doc_id}")
            else:
                print(f"  FAIL: {doc_id}")

    finally:
        await embedding_service.close()
        await solar_service.close()


if __name__ == "__main__":
    asyncio.run(main())
