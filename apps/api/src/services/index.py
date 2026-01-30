"""Vector index service using FAISS."""

import os
import uuid
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from numpy.typing import NDArray

from src.services.embedding import EmbeddingService


class IndexService:
    """Service for managing vector index using FAISS."""

    def __init__(self) -> None:
        self.index_path = Path(os.getenv("VECTOR_STORE_PATH", "data/faiss"))
        self.index_path.mkdir(parents=True, exist_ok=True)

        self.chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))
        self.dimension = 4096  # SOLAR embedding dimension

        self._index: faiss.IndexFlatIP | None = None
        self._metadata: list[dict[str, Any]] = []
        self._embedding_service = EmbeddingService()

        self._load_or_create_index()

    def _load_or_create_index(self) -> None:
        """Load existing index or create new one."""
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.npy"

        if index_file.exists() and metadata_file.exists():
            self._index = faiss.read_index(str(index_file))
            self._metadata = list(np.load(str(metadata_file), allow_pickle=True))
        else:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._metadata = []

    def _save_index(self) -> None:
        """Save index to disk."""
        if self._index is None:
            return
        faiss.write_index(self._index, str(self.index_path / "index.faiss"))
        np.save(str(self.index_path / "metadata.npy"), np.array(self._metadata, dtype=object))

    def _chunk_text(self, text: str) -> list[dict[str, Any]]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk.

        Returns:
            List of chunk dictionaries with text and position info.
        """
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Try to break at sentence boundary
            if end < len(text):
                for sep in [". ", ".\n", "\n\n"]:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + len(sep)
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start_idx": start,
                    "end_idx": end,
                })

            start = end - self.chunk_overlap if end < len(text) else len(text)

        return chunks

    async def index_document(
        self, document_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Index a document by chunking and embedding.

        Args:
            document_id: Unique document identifier.
            content: Document text content.
            metadata: Optional metadata to store with chunks.

        Returns:
            Indexing result with chunk count.
        """
        if self._index is None:
            self._load_or_create_index()

        chunks = self._chunk_text(content)
        texts = [c["text"] for c in chunks]

        embeddings = await self._embedding_service.embed_documents(texts)

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document_id}_{i}"

            # Normalize for cosine similarity
            normalized = embedding / np.linalg.norm(embedding)
            self._index.add(normalized.reshape(1, -1))

            self._metadata.append({
                "document_id": document_id,
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "start_idx": chunk["start_idx"],
                "end_idx": chunk["end_idx"],
                **(metadata or {}),
            })

        self._save_index()

        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
        }

    async def search(
        self,
        embedding: NDArray[np.float32],
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search for similar chunks.

        Args:
            embedding: Query embedding vector.
            top_k: Number of results to return.
            threshold: Minimum similarity threshold.

        Returns:
            List of matching chunks with scores.
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        # Normalize query embedding
        normalized = embedding / np.linalg.norm(embedding)

        scores, indices = self._index.search(normalized.reshape(1, -1), top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or score < threshold:
                continue
            meta = self._metadata[idx]
            results.append({
                **meta,
                "score": float(score),
            })

        return results

    async def get_chunks(self, document_id: str) -> list[dict[str, Any]]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document identifier.

        Returns:
            List of chunks for the document.
        """
        return [
            {
                "chunk_id": m["chunk_id"],
                "text": m["text"],
                "page": m.get("page"),
                "start_idx": m["start_idx"],
                "end_idx": m["end_idx"],
            }
            for m in self._metadata
            if m["document_id"] == document_id
        ]
