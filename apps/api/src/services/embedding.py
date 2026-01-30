"""Embedding service using SOLAR API."""

import os
from typing import Any

import httpx
import numpy as np
from numpy.typing import NDArray


class EmbeddingService:
    """Service for generating embeddings using Upstage SOLAR Embedding API."""

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
                timeout=30.0,
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
        Generate embeddings for multiple documents.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        client = await self._get_client()

        # Use passage model for documents
        passage_model = self.model.replace("-query", "-passage")

        response = await client.post(
            "/solar/embeddings",
            json={
                "input": texts,
                "model": passage_model,
            },
        )
        response.raise_for_status()
        data = response.json()

        return [
            np.array(item["embedding"], dtype=np.float32)
            for item in data["data"]
        ]

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
