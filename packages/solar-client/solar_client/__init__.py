"""SOLAR Client - Python wrapper for Upstage SOLAR APIs."""

from solar_client.document_parse import DocumentParseClient
from solar_client.embedding import EmbeddingClient
from solar_client.information_extract import InformationExtractClient

__version__ = "0.1.0"
__all__ = ["DocumentParseClient", "EmbeddingClient", "InformationExtractClient"]
