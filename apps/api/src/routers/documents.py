"""Document management router."""

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.models.document import (
    DocumentChunksResponse,
    DocumentIndexRequest,
    DocumentIndexResponse,
    DocumentParseResponse,
)
from src.services.index import IndexService
from src.services.solar import SolarService

router = APIRouter()


@router.post("/parse", response_model=DocumentParseResponse)
async def parse_document(
    file: Annotated[UploadFile, File(description="PDF file to parse")]
) -> DocumentParseResponse:
    """
    Parse a PDF document using SOLAR Document Parse API.

    Args:
        file: PDF file to parse.

    Returns:
        Parsed document content with structure.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        content = await file.read()
        solar_service = SolarService()
        result = await solar_service.parse_document(content, file.filename)

        return DocumentParseResponse(
            filename=file.filename,
            pages=result["pages"],
            content=result["content"],
            metadata=result.get("metadata", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/index", response_model=DocumentIndexResponse)
async def index_document(request: DocumentIndexRequest) -> DocumentIndexResponse:
    """
    Index a parsed document for evidence search.

    Args:
        request: Document content to index.

    Returns:
        Index result with document ID and chunk count.
    """
    try:
        index_service = IndexService()
        result = await index_service.index_document(
            document_id=request.document_id,
            content=request.content,
            metadata=request.metadata,
        )

        return DocumentIndexResponse(
            document_id=result["document_id"],
            chunk_count=result["chunk_count"],
            status="indexed",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{document_id}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(document_id: str) -> DocumentChunksResponse:
    """
    Get all chunks for a document.

    Args:
        document_id: Document identifier.

    Returns:
        List of document chunks.
    """
    try:
        index_service = IndexService()
        chunks = await index_service.get_chunks(document_id)

        return DocumentChunksResponse(
            document_id=document_id,
            chunks=chunks,
            total=len(chunks),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
