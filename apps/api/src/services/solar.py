"""SOLAR API service wrapper."""

import asyncio
import logging
import os
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)


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
        self.max_retries = 3
        self.base_delay = 1.0  # seconds

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=180.0,  # Increased from 60s for large PDF parsing
            )
        return self._client

    async def _request_with_retry(
        self,
        request_func: Callable[[], Any],
        operation_name: str = "API request",
    ) -> Any:
        """
        Execute a request with exponential backoff retry for transient failures.

        Args:
            request_func: Async function that makes the HTTP request.
            operation_name: Name of the operation for logging.

        Returns:
            Response from the request function.

        Raises:
            httpx.HTTPStatusError: If all retries fail.
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = await request_func()
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code

                # Retry on rate limit (429) or server errors (5xx)
                if status_code == 429 or status_code >= 500:
                    delay = self.base_delay * (2**attempt)
                    logger.warning(
                        f"{operation_name} failed with status {status_code}. "
                        f"Retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    # Don't retry client errors (4xx except 429)
                    raise
            except httpx.RequestError as e:
                # Network errors - retry
                last_exception = e
                delay = self.base_delay * (2**attempt)
                logger.warning(
                    f"{operation_name} network error: {e}. "
                    f"Retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(delay)

        logger.error(f"{operation_name} failed after {self.max_retries} retries")
        if last_exception:
            raise last_exception
        raise RuntimeError(f"{operation_name} failed after {self.max_retries} retries")

    async def parse_document(
        self, content: bytes, filename: str
    ) -> dict[str, Any]:
        """
        Parse a PDF document using SOLAR Document Parse API.

        Args:
            content: PDF file content as bytes.
            filename: Original filename.

        Returns:
            Parsed document with pages, content, grounding info, and metadata.
        """
        client = await self._get_client()

        async def make_request() -> httpx.Response:
            return await client.post(
                "https://api.upstage.ai/v1/document-ai/document-parse",
                files={"document": (filename, content, "application/pdf")},
                data={"output_formats": '["html", "text"]'},
            )

        response = await self._request_with_retry(
            make_request,
            operation_name=f"Document parse ({filename})",
        )
        data = response.json()

        return {
            "pages": data.get("num_pages", 1),
            "content": data.get("content", {}).get("text", ""),
            "html": data.get("content", {}).get("html", ""),
            "grounding": data.get("grounding", {}),
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

        async def make_request() -> httpx.Response:
            return await client.post(
                "https://api.upstage.ai/v1/document-ai/information-extraction",
                json={
                    "text": text,
                    "schema": schema,
                },
            )

        response = await self._request_with_retry(
            make_request,
            operation_name=f"Information extraction ({schema})",
        )
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
