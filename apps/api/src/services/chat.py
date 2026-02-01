"""Chat service implementing RAG-based Q&A."""

import logging

from src.models.chat import ChatMessage, ChatResponse, ChatSource
from src.services.embedding import EmbeddingService
from src.services.index import IndexService
from src.services.solar import SolarService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_WITH_DOCUMENT = """You are a helpful research assistant helping the user write their academic paper.

=== USER'S CURRENT DOCUMENT ===
{document_context}

=== REFERENCE MATERIALS ===
{context}

Instructions:
- Answer based on both the user's current document and the reference materials
- Help improve their writing with evidence from references
- Cite specific sources with page numbers when relevant
- If asked about their document, analyze it in context of the references
- Use academic tone but remain accessible"""

SYSTEM_PROMPT_NO_DOCUMENT = """You are a helpful research assistant. Answer questions based on the provided reference materials.

=== REFERENCE MATERIALS ===
{context}

Instructions:
- Be concise and direct
- Cite specific sources when possible (mention the document title or page)
- If the information isn't in the references, say so clearly
- Use academic tone but remain accessible"""

SYSTEM_PROMPT_DOCUMENT_ONLY = """You are a helpful research assistant helping the user write their academic paper.

=== USER'S CURRENT DOCUMENT ===
{document_context}

Instructions:
- Analyze and provide feedback on the user's document
- Help improve their writing, structure, and clarity
- Point out strengths and areas for improvement
- If they ask for specific evidence or citations, mention that no matching reference materials were found
- Use academic tone but remain accessible
- Respond in the same language as the user's question"""


class ChatService:
    """Service for RAG-based Q&A using evidence search and SOLAR chat."""

    def __init__(
        self,
        solar_service: SolarService,
        embedding_service: EmbeddingService,
        index_service: IndexService,
    ) -> None:
        self._solar = solar_service
        self._embedding = embedding_service
        self._index = index_service

    async def ask(
        self,
        question: str,
        top_k: int = 10,
        document_context: str | None = None,
        conversation_history: list[ChatMessage] | None = None,
    ) -> ChatResponse:
        """
        Answer a question using RAG pipeline with optional document context.

        1. Embed the question
        2. Search for relevant evidence
        3. Construct prompt with context (including user's document if provided)
        4. Generate answer via Solar chat (supports multi-turn)

        Args:
            question: User's question
            top_k: Number of evidence chunks to retrieve
            document_context: Current LaTeX document for context-aware answers
            conversation_history: Previous messages for multi-turn conversation

        Returns:
            ChatResponse with answer and sources
        """
        if conversation_history is None:
            conversation_history = []
        # Step 1: Embed the question
        query_embedding = await self._embedding.embed_query(question)

        # Step 2: Search for relevant evidence (lower threshold for broader context)
        search_results = await self._index.search(
            embedding=query_embedding,
            top_k=top_k,
            threshold=0.3,  # Lower threshold to catch more relevant results
        )

        # Step 3: Format sources and build context
        sources: list[ChatSource] = []
        context_parts: list[str] = []

        for i, result in enumerate(search_results, 1):
            # Extract document title from cite_key or document_id
            doc_id = result.get("document_id", "")
            cite_key = result.get("cite_key")
            title = self._format_document_title(cite_key or doc_id)
            page = result.get("page")
            text = result.get("text", "")

            sources.append(
                ChatSource(
                    text=text,
                    document_title=title,
                    document_id=doc_id,
                    page=page,
                    score=result.get("score", 0.0),
                )
            )

            # Build context string
            source_label = f"[Source {i}]"
            if title:
                source_label += f" {title}"
            if page:
                source_label += f", p.{page}"

            context_parts.append(f"{source_label}\n{text}")

        # Step 4: Generate answer
        if not context_parts and not document_context:
            # No sources and no document context - cannot answer
            answer = (
                "I couldn't find relevant information in the uploaded documents "
                "to answer this question. Please make sure you have uploaded "
                "reference documents related to your question."
            )
        else:
            # Build context string (may be empty if no search results)
            context = "\n\n".join(context_parts) if context_parts else ""

            # Choose prompt based on available context
            if document_context and context:
                # Both user's document and reference materials
                system_message = SYSTEM_PROMPT_WITH_DOCUMENT.format(
                    document_context=document_context,
                    context=context,
                )
            elif document_context:
                # Only user's document, no reference materials found
                system_message = SYSTEM_PROMPT_DOCUMENT_ONLY.format(
                    document_context=document_context,
                )
            else:
                # Only reference materials, no user document
                system_message = SYSTEM_PROMPT_NO_DOCUMENT.format(context=context)

            # Build messages: system + conversation history + current question
            messages: list[dict[str, str]] = [
                {"role": "system", "content": system_message}
            ]

            # Add conversation history for multi-turn
            for msg in conversation_history:
                messages.append({"role": msg.role, "content": msg.content})

            # Add current question
            messages.append({"role": "user", "content": question})

            answer = await self._solar.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )

        return ChatResponse(
            answer=answer,
            sources=sources,
            question=question,
        )

    def _format_document_title(self, cite_key: str) -> str:
        """
        Format cite_key into readable title.

        Examples:
            "Vaswani2017Attention" -> "Vaswani (2017) - Attention"
            "Brown2020Language" -> "Brown (2020) - Language"
        """
        import re

        if not cite_key:
            return ""

        # Pattern: Author(s)Year(4 digits)Title
        match = re.match(r"^([A-Za-z\-]+)(\d{4})(.+)$", cite_key)
        if match:
            authors = match.group(1)
            year = match.group(2)
            title = match.group(3)
            # Add spaces in camelCase: "LanguageModels" -> "Language Models"
            title = re.sub(r"([a-z])([A-Z])", r"\1 \2", title)
            return f"{authors} ({year}) - {title}"

        return cite_key
