"""SOLAR Information Extraction API client."""

from typing import Any

import httpx
from pydantic import BaseModel


class ExtractionResult(BaseModel):
    """Information extraction result."""

    data: dict[str, Any]
    model: str


class InformationExtractClient:
    """Client for Upstage Information Extraction API."""

    BASE_URL = "https://api.upstage.ai/v1/document-ai"

    def __init__(self, api_key: str) -> None:
        """
        Initialize information extraction client.

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
                timeout=60.0,
            )
        return self._client

    async def extract(
        self,
        text: str,
        schema: str | dict[str, Any],
    ) -> ExtractionResult:
        """
        Extract structured information from text.

        Args:
            text: Text to extract information from.
            schema: Extraction schema (predefined name or custom schema).

        Returns:
            Extraction result with structured data.
        """
        client = await self._get_client()

        response = await client.post(
            "/information-extraction",
            json={
                "text": text,
                "schema": schema,
            },
        )
        response.raise_for_status()
        data = response.json()

        return ExtractionResult(
            data=data.get("data", {}),
            model=data.get("model", ""),
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
