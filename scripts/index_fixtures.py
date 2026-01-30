#!/usr/bin/env python3
"""
Index PDFs from fixtures/papers/ into FAISS vector store.

Usage:
    cd apps/api && uv run python ../../scripts/index_fixtures.py

Environment:
    UPSTAGE_API_KEY: Required for SOLAR API
    VECTOR_STORE_PATH: Output directory (default: ../../data/faiss)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the api src to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
api_src = project_root / "apps" / "api"
sys.path.insert(0, str(api_src))

from src.services.embedding import EmbeddingService
from src.services.index import IndexService
from src.services.solar import SolarService


async def index_pdf(
    pdf_path: Path,
    solar_service: SolarService,
    index_service: IndexService,
) -> dict:
    """Parse and index a single PDF file."""
    print(f"  Parsing {pdf_path.name}...")

    with open(pdf_path, "rb") as f:
        content = f.read()

    # Parse PDF using SOLAR Document Parse API
    parsed = await solar_service.parse_document(content, pdf_path.name)

    document_id = pdf_path.stem  # filename without extension
    text_content = parsed.get("content", "")

    if not text_content.strip():
        print(f"  Warning: No text extracted from {pdf_path.name}")
        return {"document_id": document_id, "chunk_count": 0, "status": "empty"}

    print(f"  Indexing {pdf_path.name} ({len(text_content)} chars)...")

    # Index the document
    result = await index_service.index_document(
        document_id=document_id,
        content=text_content,
        metadata={
            "filename": pdf_path.name,
            "pages": parsed.get("pages", 1),
            "source": "fixtures",
        },
    )

    return {**result, "status": "indexed"}


async def main():
    """Index all PDFs from fixtures/papers/."""
    fixtures_dir = project_root / "fixtures" / "papers"
    data_dir = project_root / "data" / "faiss"
    seed_dir = project_root / "fixtures" / "seed"

    # Ensure output directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    seed_dir.mkdir(parents=True, exist_ok=True)

    # Set environment for IndexService
    os.environ.setdefault("VECTOR_STORE_PATH", str(data_dir))

    # Check for API key
    if not os.getenv("UPSTAGE_API_KEY"):
        print("Error: UPSTAGE_API_KEY environment variable is required")
        print("Set it in .env file or export it before running this script")
        sys.exit(1)

    # Find PDF files
    pdf_files = list(fixtures_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {fixtures_dir}")
        print("Add PDF files to fixtures/papers/ and run again")
        sys.exit(0)

    print(f"Found {len(pdf_files)} PDF file(s) to index:")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    print()

    # Initialize services
    embedding_service = EmbeddingService()
    index_service = IndexService(embedding_service=embedding_service)
    solar_service = SolarService()

    try:
        results = []
        for pdf_path in pdf_files:
            try:
                result = await index_pdf(pdf_path, solar_service, index_service)
                results.append(result)
                print(f"  Done: {result['chunk_count']} chunks indexed")
            except Exception as e:
                print(f"  Error processing {pdf_path.name}: {e}")
                results.append({
                    "document_id": pdf_path.stem,
                    "chunk_count": 0,
                    "status": "error",
                    "error": str(e),
                })
            print()

        # Summary
        print("=" * 50)
        print("Indexing Summary:")
        total_chunks = sum(r.get("chunk_count", 0) for r in results)
        indexed = sum(1 for r in results if r.get("status") == "indexed")
        print(f"  Total documents: {len(results)}")
        print(f"  Successfully indexed: {indexed}")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Index location: {data_dir}")
        print()

        # Copy to seed directory for pre-built index
        if indexed > 0:
            import shutil
            index_file = data_dir / "index.faiss"
            metadata_file = data_dir / "metadata.npy"

            if index_file.exists():
                shutil.copy(index_file, seed_dir / "index.faiss")
                print(f"  Copied index.faiss to {seed_dir}")
            if metadata_file.exists():
                shutil.copy(metadata_file, seed_dir / "metadata.npy")
                print(f"  Copied metadata.npy to {seed_dir}")

    finally:
        await embedding_service.close()
        await solar_service.close()


if __name__ == "__main__":
    asyncio.run(main())
