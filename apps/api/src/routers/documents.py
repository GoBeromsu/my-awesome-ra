"""Document management router."""

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from src.dependencies import get_index_service, get_solar_service
from src.models.document import (
    DocumentChunksResponse,
    DocumentDeleteResponse,
    DocumentIndexRequest,
    DocumentIndexResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentParseResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from src.services.index import IndexService
from src.services.solar import SolarService

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
DOCUMENT_ID_PATTERN = re.compile(r"^[\w\-\.]+_[a-f0-9]{12}$")

# In-memory storage for document processing status
# In production, use Redis or database
_document_status: dict[str, dict] = {}


def validate_document_id(document_id: str) -> str:
    """Validate document ID format to prevent injection."""
    if len(document_id) > 256:
        raise HTTPException(status_code=400, detail="Document ID too long")
    if not DOCUMENT_ID_PATTERN.match(document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    return document_id


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    index_service: Annotated[IndexService, Depends(get_index_service)],
) -> DocumentListResponse:
    """
    List all indexed documents.

    Returns:
        List of indexed documents with metadata.
    """
    documents = index_service.list_documents()

    return DocumentListResponse(
        documents=[
            DocumentInfo(
                document_id=doc["document_id"],
                title=doc.get("title"),
                authors=doc.get("authors"),
                chunk_count=doc["chunk_count"],
                indexed_at=doc.get("indexed_at"),
            )
            for doc in documents
        ],
        total=len(documents),
    )


@router.post("/parse", response_model=DocumentParseResponse)
async def parse_document(
    file: Annotated[UploadFile, File(description="PDF file to parse")],
    solar_service: Annotated[SolarService, Depends(get_solar_service)],
) -> DocumentParseResponse:
    """
    Parse a PDF document using SOLAR Document Parse API.

    Args:
        file: PDF file to parse.
        solar_service: Shared SolarService instance.

    Returns:
        Parsed document content with structure.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        content = await file.read()
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
async def index_document(
    request: DocumentIndexRequest,
    index_service: Annotated[IndexService, Depends(get_index_service)],
) -> DocumentIndexResponse:
    """
    Index a parsed document for evidence search.

    Args:
        request: Document content to index.
        index_service: Shared IndexService instance.

    Returns:
        Index result with document ID and chunk count.
    """
    try:
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
async def get_document_chunks(
    document_id: str,
    index_service: Annotated[IndexService, Depends(get_index_service)],
) -> DocumentChunksResponse:
    """
    Get all chunks for a document.

    Args:
        document_id: Document identifier.
        index_service: Shared IndexService instance.

    Returns:
        List of document chunks.
    """
    try:
        chunks = await index_service.get_chunks(document_id)

        return DocumentChunksResponse(
            document_id=document_id,
            chunks=chunks,
            total=len(chunks),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    index_service: Annotated[IndexService, Depends(get_index_service)],
) -> DocumentDeleteResponse:
    validate_document_id(document_id)
    """
    Delete a document and all its chunks from the index.

    Args:
        document_id: Document identifier to delete.
        index_service: Shared IndexService instance.

    Returns:
        Deletion result with chunk count.
    """
    try:
        chunks_deleted = index_service.delete_document(document_id)

        if chunks_deleted == 0:
            raise HTTPException(status_code=404, detail="Document not found")

        # Clean up status storage
        if document_id in _document_status:
            del _document_status[document_id]

        return DocumentDeleteResponse(
            document_id=document_id,
            chunks_deleted=chunks_deleted,
            status="deleted",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _process_document_in_background(
    document_id: str,
    content: bytes,
    filename: str,
    solar_service: SolarService,
    index_service: IndexService,
) -> None:
    """Background task to parse and index a document."""
    try:
        logger.info(f"Starting background processing for {document_id}")
        _document_status[document_id] = {
            "status": "processing",
            "message": "Parsing PDF...",
        }

        # Parse PDF
        parsed = await solar_service.parse_document(content, filename)

        _document_status[document_id]["message"] = "Indexing content..."

        # Index with metadata
        result = await index_service.index_document(
            document_id=document_id,
            content=parsed["content"],
            metadata={
                "title": filename.rsplit(".", 1)[0],
                "source_pdf": filename,
                "pages": parsed["pages"],
                "indexed_at": datetime.now(timezone.utc).isoformat(),
                **parsed.get("metadata", {}),
            },
        )

        _document_status[document_id] = {
            "status": "indexed",
            "message": "Indexing complete",
            "chunk_count": result["chunk_count"],
        }
        logger.info(f"Completed processing for {document_id}: {result['chunk_count']} chunks")

    except Exception as e:
        logger.error(f"Error processing {document_id}: {e}")
        _document_status[document_id] = {
            "status": "error",
            "message": str(e),
        }


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str) -> DocumentStatusResponse:
    """
    Get the processing status of a document.

    Args:
        document_id: Document identifier.

    Returns:
        Current processing status.
    """
    validate_document_id(document_id)
    if document_id not in _document_status:
        raise HTTPException(status_code=404, detail="Document not found")

    status_info = _document_status[document_id]
    return DocumentStatusResponse(
        document_id=document_id,
        status=status_info["status"],
        message=status_info.get("message"),
        chunk_count=status_info.get("chunk_count"),
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_and_index_document(
    file: Annotated[UploadFile, File(description="PDF file to upload and index")],
    background_tasks: BackgroundTasks,
    solar_service: Annotated[SolarService, Depends(get_solar_service)],
    index_service: Annotated[IndexService, Depends(get_index_service)],
) -> DocumentUploadResponse:
    """
    Upload a PDF and start background processing.

    This endpoint:
    1. Accepts the PDF file
    2. Returns immediately with a document ID
    3. Processes (parse + index) in the background

    Poll GET /documents/{id}/status to check processing status.

    Args:
        file: PDF file to upload.
        background_tasks: FastAPI background tasks.
        solar_service: Shared SolarService instance.
        index_service: Shared IndexService instance.

    Returns:
        Document ID and initial processing status.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        content = await file.read()

        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
            )

        # Generate document_id from filename hash
        file_hash = hashlib.sha256(content).hexdigest()[:12]
        # Sanitize filename for document ID
        safe_name = re.sub(r"[^\w\-\.]", "_", file.filename.rsplit(".", 1)[0])
        document_id = f"{safe_name}_{file_hash}"

        # Check if already processing or indexed
        if document_id in _document_status:
            current = _document_status[document_id]
            if current["status"] == "processing":
                return DocumentUploadResponse(
                    document_id=document_id,
                    status="processing",
                    message="Document is already being processed",
                )
            if current["status"] == "indexed":
                return DocumentUploadResponse(
                    document_id=document_id,
                    status="indexed",
                    message="Document is already indexed",
                )

        # Initialize status
        _document_status[document_id] = {
            "status": "processing",
            "message": "Queued for processing",
        }

        # Add background task
        background_tasks.add_task(
            _process_document_in_background,
            document_id,
            content,
            file.filename,
            solar_service,
            index_service,
        )

        return DocumentUploadResponse(
            document_id=document_id,
            status="processing",
            message="Document queued for processing",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/upload/sync", response_model=DocumentIndexResponse)
async def upload_and_index_document_sync(
    file: Annotated[UploadFile, File(description="PDF file to upload and index")],
    solar_service: Annotated[SolarService, Depends(get_solar_service)],
    index_service: Annotated[IndexService, Depends(get_index_service)],
) -> DocumentIndexResponse:
    """
    Upload a PDF, parse it, and index it synchronously.

    This is a synchronous version that waits for completion.
    Use POST /documents/upload for background processing.

    Args:
        file: PDF file to upload.
        solar_service: Shared SolarService instance.
        index_service: Shared IndexService instance.

    Returns:
        Index result with document ID and chunk count.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        content = await file.read()

        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
            )

        # Generate document_id from filename hash
        file_hash = hashlib.sha256(content).hexdigest()[:12]
        # Sanitize filename for document ID
        safe_name = re.sub(r"[^\w\-\.]", "_", file.filename.rsplit(".", 1)[0])
        document_id = f"{safe_name}_{file_hash}"

        # Parse PDF
        parsed = await solar_service.parse_document(content, file.filename)

        # Index with metadata
        result = await index_service.index_document(
            document_id=document_id,
            content=parsed["content"],
            metadata={
                "title": file.filename.rsplit(".", 1)[0],
                "source_pdf": file.filename,
                "pages": parsed["pages"],
                "indexed_at": datetime.now(timezone.utc).isoformat(),
                **parsed.get("metadata", {}),
            },
        )

        # Update status
        _document_status[document_id] = {
            "status": "indexed",
            "message": "Indexing complete",
            "chunk_count": result["chunk_count"],
        }

        return DocumentIndexResponse(
            document_id=result["document_id"],
            chunk_count=result["chunk_count"],
            status="indexed",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
