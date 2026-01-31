"""Integration tests for document upload and management flow."""

import io
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_services(mock_embedding_service):
    """Set up mocked services on app state."""
    mock_index = MagicMock()
    mock_index.list_documents = MagicMock(return_value=[
        {
            "document_id": "test-doc-001",
            "title": "Test Document",
            "authors": "Test Author",
            "chunk_count": 5,
            "indexed_at": "2024-01-01T00:00:00Z",
        }
    ])
    mock_index.get_chunks = AsyncMock(return_value=[
        {
            "chunk_id": "test-doc-001_0",
            "text": "Test chunk content",
            "page": 1,
            "start_idx": 0,
            "end_idx": 18,
        }
    ])

    mock_solar = MagicMock()
    mock_solar.parse_document = AsyncMock(return_value={
        "content": "Parsed document content.",
        "pages": 1,
        "metadata": {"title": "Test"},
    })

    app.state.embedding_service = mock_embedding_service
    app.state.index_service = mock_index
    app.state.solar_service = mock_solar

    return {"index": mock_index, "solar": mock_solar}


class TestDocumentUpload:
    """Tests for document upload endpoint."""

    def test_upload_returns_processing_status(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify upload returns processing status with document ID."""
        pdf_content = b"%PDF-1.4 fake pdf content for testing"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}

        response = client.post("/documents/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["status"] == "processing"
        assert "message" in data

    def test_upload_rejects_non_pdf(self, client: TestClient, mock_services) -> None:
        """Verify upload rejects non-PDF files with 400 error."""
        text_content = b"This is not a PDF"
        files = {"file": ("document.txt", io.BytesIO(text_content), "text/plain")}

        response = client.post("/documents/upload", files=files)

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_rejects_empty_filename(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify upload rejects files without .pdf extension."""
        pdf_content = b"%PDF-1.4 content"
        files = {"file": ("noextension", io.BytesIO(pdf_content), "application/pdf")}

        response = client.post("/documents/upload", files=files)

        assert response.status_code == 400

    def test_upload_generates_document_id(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify document ID is generated from filename hash."""
        pdf_content = b"%PDF-1.4 unique content 12345"
        files = {"file": ("my_paper.pdf", io.BytesIO(pdf_content), "application/pdf")}

        response = client.post("/documents/upload", files=files)

        assert response.status_code == 200
        doc_id = response.json()["document_id"]
        # Should contain sanitized filename
        assert "my_paper" in doc_id
        # Should have hash suffix
        assert "_" in doc_id


class TestDocumentList:
    """Tests for document listing endpoint."""

    def test_list_documents_endpoint(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify GET /documents returns indexed documents."""
        response = client.get("/documents")

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert data["total"] == 1
        assert data["documents"][0]["document_id"] == "test-doc-001"

    def test_list_documents_includes_metadata(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify document list includes metadata fields."""
        response = client.get("/documents")

        assert response.status_code == 200
        doc = response.json()["documents"][0]

        assert "title" in doc
        assert "chunk_count" in doc
        assert doc["chunk_count"] == 5


class TestDocumentChunks:
    """Tests for document chunks endpoint."""

    def test_get_chunks_returns_document_chunks(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify GET /documents/{id}/chunks returns chunks."""
        response = client.get("/documents/test-doc-001_abc123abc123/chunks")

        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total" in data
        assert data["total"] == 1

    def test_get_chunks_includes_text_and_position(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify chunks include text and position info."""
        response = client.get("/documents/test-doc-001_abc123abc123/chunks")

        chunk = response.json()["chunks"][0]
        assert "text" in chunk
        assert "start_idx" in chunk
        assert "end_idx" in chunk
        assert "page" in chunk


class TestDocumentValidation:
    """Tests for document ID validation."""

    def test_invalid_document_id_format(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify invalid document ID format is rejected."""
        # Missing hash suffix
        response = client.get("/documents/invalid-id/status")
        assert response.status_code == 400

    def test_document_id_too_long(
        self, client: TestClient, mock_services
    ) -> None:
        """Verify overly long document ID is rejected."""
        long_id = "a" * 300 + "_123456789012"
        response = client.get(f"/documents/{long_id}/status")
        assert response.status_code == 400


class TestDocumentIntegration:
    """Integration tests using seed fixtures."""

    def test_list_documents_with_seed(self, client_with_seed: TestClient) -> None:
        """Verify list endpoint returns seed documents."""
        response = client_with_seed.get("/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

        # Should contain seed document
        doc_ids = [d["document_id"] for d in data["documents"]]
        assert "test-doc-001" in doc_ids

    def test_get_chunks_with_seed(self, client_with_seed: TestClient) -> None:
        """Verify chunks endpoint works with seed data."""
        response = client_with_seed.get("/documents/test-doc-001_abc123abc123/chunks")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-001_abc123abc123"
