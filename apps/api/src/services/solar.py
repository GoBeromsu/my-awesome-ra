"""SOLAR API service wrapper."""

import os
from typing import Any

import httpx


class SolarService:
    """Service for interacting with Upstage SOLAR APIs."""

    def __init__(self) -> None:
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY environment variable is required")
        self.base_url = os.getenv(
            "UPSTAGE_API_BASE_URL", "https://api.upstage.ai/v1/solar"
        )
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=60.0,
            )
        return self._client

    async def parse_document(
        self, content: bytes, filename: str
    ) -> dict[str, Any]:
        """
        Parse a PDF document using SOLAR Document Parse API.

        Args:
            content: PDF file content as bytes.
            filename: Original filename.

        Returns:
            Parsed document with pages, content, and metadata.
        """
        client = await self._get_client()

        # Use Upstage Document Parse API
        # https://console.upstage.ai/docs/capabilities/document-parse
        response = await client.post(
            "https://api.upstage.ai/v1/document-ai/document-parse",
            files={"document": (filename, content, "application/pdf")},
            data={"output_formats": "['text']"},
        )
        response.raise_for_status()
        data = response.json()

        return {
            "pages": data.get("num_pages", 1),
            "content": data.get("content", {}).get("text", ""),
            "metadata": {
                "filename": filename,
                "model": data.get("model", ""),
            },
        }

    async def extract_information(
        self, text: str, schema: str
    ) -> dict[str, Any]:
        """
        Extract structured information from text using SOLAR Information Extraction API.

        Args:
            text: Text to extract information from.
            schema: Extraction schema type (e.g., "citation").

        Returns:
            Extracted information based on schema.
        """
        client = await self._get_client()

        # Use Upstage Information Extraction API
        # https://console.upstage.ai/docs/capabilities/information-extraction
        response = await client.post(
            "https://api.upstage.ai/v1/document-ai/information-extraction",
            json={
                "text": text,
                "schema": schema,
            },
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
