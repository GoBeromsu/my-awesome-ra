"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import citations, documents, evidence
from src.services.embedding import EmbeddingService
from src.services.index import IndexService
from src.services.solar import SolarService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan: initialization on startup, cleanup on shutdown.

    Creates shared service instances and ensures proper cleanup of HTTP clients.
    """
    # Startup: Initialize services
    embedding_service = EmbeddingService()
    # Pass embedding_service to avoid creating duplicate instances
    index_service = IndexService(embedding_service=embedding_service)
    solar_service = SolarService()

    # Store services in app state for dependency injection
    app.state.embedding_service = embedding_service
    app.state.index_service = index_service
    app.state.solar_service = solar_service

    yield

    # Shutdown: Clean up resources
    await embedding_service.close()
    await solar_service.close()


app = FastAPI(
    title="My Awesome RA API",
    description="AI Agent service for reference-grounded LaTeX paper writing",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration with security-first defaults
# Development: Allow localhost origins
# Production: Allow configurable FRONTEND_URL
def get_allowed_origins() -> list[str]:
    """Get allowed CORS origins from environment variables.

    Development: Allows localhost on common dev ports
    Production: Allows configured FRONTEND_URL only

    Returns:
        List of allowed origin URLs
    """
    allowed_origins = []

    # Always allow localhost for development
    allowed_origins.extend([
        "http://localhost",           # Overleaf dev server
        "http://localhost:80",        # Overleaf dev server (explicit)
        "http://localhost:3000",      # React dev server
        "http://localhost:5173",      # Vite dev server
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ])

    # Add production frontend URL if configured
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        allowed_origins.append(frontend_url)

    return allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,  # Never allow credentials with CORS
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(citations.router, prefix="/citations", tags=["citations"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
