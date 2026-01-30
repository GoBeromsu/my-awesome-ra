"""Evidence search models."""

from pydantic import BaseModel, Field


class EvidenceSearchRequest(BaseModel):
    """Request model for evidence search."""

    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold"
    )
    document_ids: list[str] | None = Field(
        default=None, description="Optional filter by document IDs"
    )


class EvidenceResult(BaseModel):
    """Single evidence result."""

    document_id: str = Field(..., description="Source document identifier")
    chunk_id: str = Field(..., description="Chunk identifier within document")
    text: str = Field(..., description="Evidence text content")
    page: int | None = Field(default=None, description="Page number in source document")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    metadata: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Additional metadata"
    )


class EvidenceSearchResponse(BaseModel):
    """Response model for evidence search."""

    results: list[EvidenceResult] = Field(..., description="List of evidence results")
    query: str = Field(..., description="Original search query")
    total: int = Field(..., ge=0, description="Total number of results")
