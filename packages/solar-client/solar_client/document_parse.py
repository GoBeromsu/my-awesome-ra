"""SOLAR Document Parse API client."""

from typing import Any

import httpx
from pydantic import BaseModel


class ParsedDocument(BaseModel):
    """Parsed document response."""

    content: str
    num_pages: int
    metadata: dict[str, Any]


class DocumentParseClient:
    """Client for Upstage Document Parse API."""

    BASE_URL = "https://api.upstage.ai/v1/document-ai"

    def __init__(self, api_key: str) -> None:
        """
        Initialize document parse client.

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
                timeout=120.0,
            )
        return self._client

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        output_formats: list[str] | None = None,
    ) -> ParsedDocument:
        """
        Parse a PDF document.

        Args:
            file_content: PDF file content as bytes.
            filename: Original filename.
            output_formats: Output formats (default: ["text"]).

        Returns:
            Parsed document with content and metadata.
        """
        client = await self._get_client()

        formats = output_formats or ["text"]

        response = await client.post(
            "/document-parse",
            files={"document": (filename, file_content, "application/pdf")},
            data={"output_formats": str(formats)},
        )
        response.raise_for_status()
        data = response.json()

        return ParsedDocument(
            content=data.get("content", {}).get("text", ""),
            num_pages=data.get("num_pages", 1),
            metadata={
                "filename": filename,
                "model": data.get("model", ""),
                "api_version": data.get("api_version", ""),
            },
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
