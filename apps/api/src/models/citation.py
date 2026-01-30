"""Citation extraction models."""

from pydantic import BaseModel, Field


class CitationExtractRequest(BaseModel):
    """Request model for citation extraction."""

    text: str = Field(..., description="Text content to extract citations from")
    extraction_schema: str | None = Field(
        default=None, description="Custom extraction schema"
    )


class Citation(BaseModel):
    """Single extracted citation."""

    title: str = Field(..., description="Paper title")
    authors: list[str] = Field(default_factory=list, description="List of authors")
    year: int | None = Field(default=None, description="Publication year")
    venue: str | None = Field(default=None, description="Publication venue")
    doi: str | None = Field(default=None, description="Digital Object Identifier")
    raw_text: str = Field(default="", description="Original citation text")


class CitationExtractResponse(BaseModel):
    """Response model for citation extraction."""

    citations: list[Citation] = Field(..., description="Extracted citations")
    total: int = Field(..., ge=0, description="Total number of citations")
