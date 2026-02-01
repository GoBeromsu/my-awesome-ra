"""Chat models for RAG-based Q&A."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single message in conversation history."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Request for chat/ask endpoint."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="User's question to answer using RAG",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of evidence chunks to retrieve",
    )
    document_context: str | None = Field(
        None,
        max_length=100000,
        description="Current LaTeX document content for context-aware Q&A",
    )
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation messages for multi-turn chat",
    )


class ChatSource(BaseModel):
    """A source/reference used to generate the answer."""

    text: str = Field(..., description="Source text content")
    document_title: str | None = Field(None, description="Title of source document")
    document_id: str | None = Field(None, description="Document ID for linking")
    page: int | None = Field(None, description="Page number in source document")
    score: float = Field(..., description="Relevance score (0-1)")


class ChatResponse(BaseModel):
    """Response from chat/ask endpoint."""

    answer: str = Field(..., description="AI-generated answer based on sources")
    sources: list[ChatSource] = Field(
        default_factory=list,
        description="Evidence sources used for the answer",
    )
    question: str = Field(..., description="Original question")
