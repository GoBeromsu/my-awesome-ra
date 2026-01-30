"""Evidence search router."""

from fastapi import APIRouter, HTTPException

from src.models.evidence import EvidenceSearchRequest, EvidenceSearchResponse, EvidenceResult
from src.services.embedding import EmbeddingService
from src.services.index import IndexService

router = APIRouter()


@router.post("/search", response_model=EvidenceSearchResponse)
async def search_evidence(request: EvidenceSearchRequest) -> EvidenceSearchResponse:
    """
    Search for relevant evidence spans from reference documents.

    Args:
        request: Search request containing query text and optional filters.

    Returns:
        List of evidence results with relevance scores.
    """
    try:
        embedding_service = EmbeddingService()
        index_service = IndexService()

        query_embedding = await embedding_service.embed_query(request.query)
        results = await index_service.search(
            embedding=query_embedding,
            top_k=request.top_k,
            threshold=request.threshold,
        )

        return EvidenceSearchResponse(
            results=[
                EvidenceResult(
                    document_id=r["document_id"],
                    chunk_id=r["chunk_id"],
                    text=r["text"],
                    page=r.get("page"),
                    score=r["score"],
                    metadata=r.get("metadata", {}),
                )
                for r in results
            ],
            query=request.query,
            total=len(results),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
