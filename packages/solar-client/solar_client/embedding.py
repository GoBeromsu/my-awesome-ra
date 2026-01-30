"""SOLAR Embedding API client."""

from typing import Literal

import httpx
from pydantic import BaseModel


class EmbeddingResponse(BaseModel):
    """Response from embedding API."""

    embedding: list[float]
    model: str
    usage: dict[str, int]


class EmbeddingClient:
    """Client for Upstage SOLAR Embedding API."""

    BASE_URL = "https://api.upstage.ai/v1/solar"

    def __init__(self, api_key: str) -> None:
        """
        Initialize embedding client.

        Args:
            api_key: Upstage API key.
        """
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
        return self._client

    async def embed(
        self,
        text: str | list[str],
        model: Literal["solar-embedding-1-large-query", "solar-embedding-1-large-passage"]
        = "solar-embedding-1-large-query",
    ) -> list[EmbeddingResponse]:
        """
        Generate embeddings for text.

        Args:
            text: Single text or list of texts to embed.
            model: Embedding model to use.

        Returns:
            List of embedding responses.
        """
        client = await self._get_client()

        response = await client.post(
            "/embeddings",
            json={
                "input": text,
                "model": model,
            },
        )
        response.raise_for_status()
        data = response.json()

        return [
            EmbeddingResponse(
                embedding=item["embedding"],
                model=data["model"],
                usage=data["usage"],
            )
            for item in data["data"]
        ]

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
