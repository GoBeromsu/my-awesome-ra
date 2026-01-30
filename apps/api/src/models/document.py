"""Document management models."""

from pydantic import BaseModel, Field


class DocumentParseResponse(BaseModel):
    """Response model for document parsing."""

    filename: str = Field(..., description="Original filename")
    pages: int = Field(..., ge=1, description="Number of pages")
    content: str = Field(..., description="Extracted text content")
    metadata: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Document metadata"
    )


class DocumentIndexRequest(BaseModel):
    """Request model for document indexing."""

    document_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document text content to index")
    metadata: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Additional metadata"
    )


class DocumentIndexResponse(BaseModel):
    """Response model for document indexing."""

    document_id: str = Field(..., description="Document identifier")
    chunk_count: int = Field(..., ge=0, description="Number of chunks created")
    status: str = Field(..., description="Indexing status")


class DocumentChunk(BaseModel):
    """Single document chunk."""

    chunk_id: str = Field(..., description="Chunk identifier")
    text: str = Field(..., description="Chunk text content")
    page: int | None = Field(default=None, description="Source page number")
    start_idx: int = Field(..., ge=0, description="Start character index")
    end_idx: int = Field(..., ge=0, description="End character index")


class DocumentChunksResponse(BaseModel):
    """Response model for document chunks."""

    document_id: str = Field(..., description="Document identifier")
    chunks: list[DocumentChunk] = Field(..., description="List of chunks")
    total: int = Field(..., ge=0, description="Total number of chunks")
