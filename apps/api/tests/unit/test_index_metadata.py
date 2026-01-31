"""Unit tests for index metadata operations."""

import os
from pathlib import Path

import pytest


class TestListDocuments:
    """Tests for IndexService.list_documents method."""

    @pytest.mark.asyncio
    async def test_list_documents_returns_indexed(self, isolated_index_service) -> None:
        """Verify list_documents returns all indexed documents."""
        # Index some documents
        await isolated_index_service.index_document(
            document_id="list-doc-001",
            content="First document content.",
            metadata={"title": "First Doc"},
        )
        await isolated_index_service.index_document(
            document_id="list-doc-002",
            content="Second document content.",
            metadata={"title": "Second Doc"},
        )

        docs = isolated_index_service.list_documents()

        assert len(docs) == 2
        doc_ids = {d["document_id"] for d in docs}
        assert doc_ids == {"list-doc-001", "list-doc-002"}

    def test_list_documents_empty_index(self, isolated_index_service) -> None:
        """Verify empty list returned for empty index."""
        docs = isolated_index_service.list_documents()
        assert docs == []

    @pytest.mark.asyncio
    async def test_list_documents_includes_chunk_count(
        self, isolated_index_service
    ) -> None:
        """Verify chunk_count is included in document info."""
        await isolated_index_service.index_document(
            document_id="count-doc-001",
            content="Content for chunk counting. " * 30,
        )

        docs = isolated_index_service.list_documents()

        assert len(docs) == 1
        assert "chunk_count" in docs[0]
        assert docs[0]["chunk_count"] > 0


class TestGetChunks:
    """Tests for IndexService.get_chunks method."""

    @pytest.mark.asyncio
    async def test_get_chunks_returns_document_chunks(
        self, isolated_index_service
    ) -> None:
        """Verify get_chunks returns all chunks for a document."""
        result = await isolated_index_service.index_document(
            document_id="chunks-doc-001",
            content="Content for chunk retrieval. " * 30,
        )

        chunks = await isolated_index_service.get_chunks("chunks-doc-001")

        assert len(chunks) == result["chunk_count"]
        for chunk in chunks:
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert chunk["chunk_id"].startswith("chunks-doc-001_")

    @pytest.mark.asyncio
    async def test_get_chunks_nonexistent_returns_empty(
        self, isolated_index_service
    ) -> None:
        """Verify get_chunks returns empty for non-existent document."""
        chunks = await isolated_index_service.get_chunks("nonexistent-doc")
        assert chunks == []

    @pytest.mark.asyncio
    async def test_get_chunks_includes_positions(self, isolated_index_service) -> None:
        """Verify chunk position info is included."""
        await isolated_index_service.index_document(
            document_id="pos-doc-001",
            content="Short content for testing.",
        )

        chunks = await isolated_index_service.get_chunks("pos-doc-001")

        assert len(chunks) >= 1
        chunk = chunks[0]
        assert "start_idx" in chunk
        assert "end_idx" in chunk
        assert chunk["start_idx"] >= 0
        assert chunk["end_idx"] > chunk["start_idx"]


class TestMetadataPersistence:
    """Tests for metadata persistence to disk."""

    @pytest.mark.asyncio
    async def test_metadata_persisted_to_disk(
        self, isolated_index_service, temp_index_path: Path
    ) -> None:
        """Verify metadata.npy is created after indexing."""
        await isolated_index_service.index_document(
            document_id="persist-doc-001",
            content="Content to persist. " * 10,
        )

        metadata_file = temp_index_path / "metadata.npy"
        assert metadata_file.exists(), "metadata.npy not created"

    @pytest.mark.asyncio
    async def test_index_reload_preserves_data(
        self, temp_index_path: Path, mock_embedding_service
    ) -> None:
        """Verify data persists across service restarts."""
        original_seed = os.environ.get("SEED_INDEX_PATH")
        os.environ["VECTOR_STORE_PATH"] = str(temp_index_path)
        os.environ["SEED_INDEX_PATH"] = str(temp_index_path / "nonexistent")

        from src.services.index import IndexService

        # Create and index with first instance
        service1 = IndexService(embedding_service=mock_embedding_service)
        await service1.index_document(
            document_id="reload-doc-001",
            content="Content to reload. " * 10,
        )
        original_count = service1._index.ntotal

        # Create new instance - should load persisted data
        service2 = IndexService(embedding_service=mock_embedding_service)

        assert service2._index.ntotal == original_count
        docs = service2.list_documents()
        assert len(docs) == 1
        assert docs[0]["document_id"] == "reload-doc-001"

        # Restore
        if original_seed is not None:
            os.environ["SEED_INDEX_PATH"] = original_seed
        else:
            os.environ.pop("SEED_INDEX_PATH", None)


class TestSeedFixtures:
    """Tests for seed fixture loading."""

    def test_seed_fixture_loaded_correctly(self, seed_index_service) -> None:
        """Verify seed fixtures load with expected chunk count."""
        # Seed index should have 17 chunks
        assert seed_index_service._index.ntotal == 17, (
            f"Expected 17 chunks in seed, got {seed_index_service._index.ntotal}"
        )

    def test_seed_fixture_has_metadata(self, seed_index_service) -> None:
        """Verify seed fixtures include metadata."""
        assert len(seed_index_service._metadata) == 17

        # Check metadata structure
        for meta in seed_index_service._metadata:
            assert "document_id" in meta
            assert "chunk_id" in meta
            assert "text" in meta

    def test_seed_fixture_documents_listable(self, seed_index_service) -> None:
        """Verify seed documents appear in list_documents."""
        docs = seed_index_service.list_documents()
        assert len(docs) >= 1

        # Should have test-doc-001 from seed
        doc_ids = [d["document_id"] for d in docs]
        assert "test-doc-001" in doc_ids

    @pytest.mark.asyncio
    async def test_seed_fixture_searchable(self, seed_index_service) -> None:
        """Verify seed data is searchable."""
        import numpy as np

        # Use a vector similar to existing data to ensure match
        if seed_index_service._index.ntotal > 0:
            existing = seed_index_service._index.reconstruct(0)
            query = existing + np.random.default_rng(42).random(4096).astype(np.float32) * 0.01
            query = query / np.linalg.norm(query)
        else:
            query = np.random.default_rng(42).random(4096).astype(np.float32)
            query = query / np.linalg.norm(query)

        results = await seed_index_service.search(
            embedding=query,
            top_k=5,
            threshold=-1.0,  # Accept all results for testing
        )

        assert len(results) > 0
