"""Chat router for RAG-based Q&A."""

from fastapi import APIRouter, Depends, HTTPException, Request

from src.models.chat import ChatRequest, ChatResponse
from src.services.chat import ChatService

router = APIRouter()


def get_chat_service(request: Request) -> ChatService:
    """Get ChatService from app state."""
    return request.app.state.chat_service


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Ask a question and get an AI-generated answer based on uploaded documents.

    The RAG pipeline:
    1. Embeds your question
    2. Searches for relevant evidence in indexed documents
    3. Uses Solar LLM to generate a grounded answer

    Returns the answer along with source references.
    """
    try:
        return await chat_service.ask(
            question=request.question,
            top_k=request.top_k,
            document_context=request.document_context,
            conversation_history=request.conversation_history,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}",
        ) from e
