"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import citations, documents, evidence

app = FastAPI(
    title="My Awesome RA API",
    description="AI Agent service for reference-grounded LaTeX paper writing",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(citations.router, prefix="/citations", tags=["citations"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
