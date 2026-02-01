"""Embedding service using SOLAR API."""

import os

import httpx
import numpy as np
from numpy.typing import NDArray


class EmbeddingService:
    """Service for generating embeddings using Upstage SOLAR Embedding API."""

    # Batch size for processing large document sets to avoid timeouts
    BATCH_SIZE = 5

    def __init__(self) -> None:
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY environment variable is required")
        self.model = os.getenv("EMBEDDING_MODEL", "solar-embedding-1-large-query")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.upstage.ai/v1",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0,  # Increased from 30s for large documents
            )
        return self._client

    async def embed_query(self, text: str) -> NDArray[np.float32]:
        """
        Generate embedding for a query text.

        Args:
            text: Query text to embed.

        Returns:
            Embedding vector as numpy array.
        """
        client = await self._get_client()

        # Use Upstage Embedding API
        # https://console.upstage.ai/docs/capabilities/embeddings
        response = await client.post(
            "/solar/embeddings",
            json={
                "input": text,
                "model": self.model,
            },
        )
        response.raise_for_status()
        data = response.json()

        embedding = data["data"][0]["embedding"]
        return np.array(embedding, dtype=np.float32)

    async def embed_documents(
        self, texts: list[str]
    ) -> list[NDArray[np.float32]]:
        """
        Generate embeddings for multiple documents with batch processing.

        Processes texts in batches to avoid API timeouts for large documents.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        client = await self._get_client()

        # Use passage model for documents
        passage_model = self.model.replace("-query", "-passage")

        # Process in batches to avoid timeout
        all_embeddings: list[NDArray[np.float32]] = []

        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i : i + self.BATCH_SIZE]

            response = await client.post(
                "/solar/embeddings",
                json={
                    "input": batch,
                    "model": passage_model,
                },
            )
            response.raise_for_status()
            data = response.json()

            batch_embeddings = [
                np.array(item["embedding"], dtype=np.float32)
                for item in data["data"]
            ]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
