"""Tests for evidence search router."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client with mocked services."""
    return TestClient(app)


@pytest.fixture
def mock_embedding_service():
    """Create mock embedding service."""
    mock = AsyncMock()
    mock.embed_query = AsyncMock(return_value=[0.1] * 1024)
    return mock


@pytest.fixture
def mock_index_service():
    """Create mock index service."""
    mock = AsyncMock()
    mock.search = AsyncMock(return_value=[
        {
            "document_id": "doc-1",
            "chunk_id": "chunk-1",
            "text": "This is a test evidence span.",
            "score": 0.95,
            "page": 1,
            "title": "Test Document",
            "authors": "Author One",
            "year": 2024,
            "source_pdf": "test.pdf",
        }
    ])
    return mock


def test_evidence_search_success(
    client: TestClient,
    mock_embedding_service,
    mock_index_service,
) -> None:
    """Test successful evidence search."""
    # Mock the app state services
    app.state.embedding_service = mock_embedding_service
    app.state.index_service = mock_index_service

    response = client.post(
        "/evidence/search",
        json={"query": "test query", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test query"
    assert data["total"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["document_id"] == "doc-1"
    assert data["results"][0]["text"] == "This is a test evidence span."
    assert data["results"][0]["score"] == 0.95


def test_evidence_search_empty_results(
    client: TestClient,
    mock_embedding_service,
) -> None:
    """Test evidence search with no results."""
    mock_index = AsyncMock()
    mock_index.search = AsyncMock(return_value=[])

    app.state.embedding_service = mock_embedding_service
    app.state.index_service = mock_index

    response = client.post(
        "/evidence/search",
        json={"query": "nonexistent topic"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


def test_evidence_search_with_threshold(
    client: TestClient,
    mock_embedding_service,
    mock_index_service,
) -> None:
    """Test evidence search with custom threshold."""
    app.state.embedding_service = mock_embedding_service
    app.state.index_service = mock_index_service

    response = client.post(
        "/evidence/search",
        json={"query": "test", "top_k": 10, "threshold": 0.8},
    )

    assert response.status_code == 200
    mock_index_service.search.assert_called_once()
    call_kwargs = mock_index_service.search.call_args[1]
    assert call_kwargs["threshold"] == 0.8
    assert call_kwargs["top_k"] == 10


def test_evidence_search_invalid_request(client: TestClient) -> None:
    """Test evidence search with invalid request body."""
    response = client.post(
        "/evidence/search",
        json={},  # Missing required 'query' field
    )

    assert response.status_code == 422  # Validation error


def test_evidence_search_service_error(
    client: TestClient,
    mock_embedding_service,
) -> None:
    """Test evidence search when service raises error."""
    mock_embedding_service.embed_query = AsyncMock(
        side_effect=Exception("Embedding service unavailable")
    )
    app.state.embedding_service = mock_embedding_service

    response = client.post(
        "/evidence/search",
        json={"query": "test"},
    )

    assert response.status_code == 500
    assert "error" in response.json()["detail"].lower()
