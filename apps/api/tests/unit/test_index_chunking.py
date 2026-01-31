"""Unit tests for text chunking functionality."""

import pytest


class TestChunkText:
    """Tests for IndexService._chunk_text method."""

    def test_chunk_text_respects_max_size(self, isolated_index_service) -> None:
        """Verify that chunks do not exceed max chunk size (500 chars)."""
        long_text = "This is a sentence. " * 100  # ~2000 chars

        chunks = isolated_index_service._chunk_text(long_text)

        for chunk in chunks:
            assert len(chunk["text"]) <= 500, (
                f"Chunk exceeds max size: {len(chunk['text'])} chars"
            )

    def test_chunk_text_maintains_overlap(self, isolated_index_service) -> None:
        """Verify overlapping content between consecutive chunks."""
        text = "Sentence one. " * 20 + "Unique middle. " + "Sentence end. " * 20

        chunks = isolated_index_service._chunk_text(text)

        if len(chunks) >= 2:
            # Check that consecutive chunks share content
            for i in range(len(chunks) - 1):
                current_end = chunks[i]["end_idx"]
                next_start = chunks[i + 1]["start_idx"]
                # Overlap means next chunk starts before current ends
                assert next_start < current_end, (
                    f"No overlap between chunk {i} and {i + 1}"
                )

    def test_chunk_text_breaks_at_sentence(self, isolated_index_service) -> None:
        """Verify preference for sentence boundary breaks."""
        # Text with clear sentence boundaries
        text = "First sentence here. Second sentence follows. Third one too. Fourth."

        chunks = isolated_index_service._chunk_text(text)

        # With short text, should be single chunk
        if len(chunks) == 1:
            assert chunks[0]["text"] == text.strip()
        else:
            # Multi-chunk: verify breaks at periods when possible
            for chunk in chunks:
                chunk_text = chunk["text"]
                # If not the last chunk, should end with sentence terminator
                if chunk != chunks[-1] and len(chunk_text) > 10:
                    assert chunk_text.endswith((".")) or chunk_text.strip().endswith(
                        ("\n")
                    ), f"Chunk did not break at sentence: '{chunk_text[-20:]}'"

    def test_chunk_text_empty_input(self, isolated_index_service) -> None:
        """Verify empty input returns empty list."""
        chunks = isolated_index_service._chunk_text("")
        assert chunks == []

    def test_chunk_text_whitespace_input(self, isolated_index_service) -> None:
        """Verify whitespace-only input returns empty list."""
        chunks = isolated_index_service._chunk_text("   \n\t  ")
        assert chunks == []

    def test_chunk_text_short_input_single(self, isolated_index_service) -> None:
        """Verify short text produces single chunk."""
        short_text = "This is a short text that fits in one chunk."

        chunks = isolated_index_service._chunk_text(short_text)

        assert len(chunks) == 1
        assert chunks[0]["text"] == short_text
        assert chunks[0]["start_idx"] == 0
        assert chunks[0]["end_idx"] == len(short_text)

    def test_chunk_text_preserves_all_content(self, isolated_index_service) -> None:
        """Verify no content is lost during chunking."""
        # Create text with unique markers
        markers = [f"[MARKER_{i}]" for i in range(50)]
        text = " ".join(markers) + ". " + "Additional padding. " * 100

        chunks = isolated_index_service._chunk_text(text)

        # Combine all chunk texts
        all_chunk_text = " ".join(c["text"] for c in chunks)

        # All markers should be present (at least once due to overlap)
        for marker in markers:
            assert marker in all_chunk_text, f"Lost content: {marker}"

    def test_chunk_text_position_tracking(self, isolated_index_service) -> None:
        """Verify start_idx and end_idx accurately track positions."""
        text = "First part. Second part. Third part. Fourth part."

        chunks = isolated_index_service._chunk_text(text)

        for chunk in chunks:
            # Extract text using tracked positions
            extracted = text[chunk["start_idx"] : chunk["end_idx"]].strip()
            assert extracted == chunk["text"], (
                f"Position mismatch: '{extracted}' vs '{chunk['text']}'"
            )

    def test_chunk_text_handles_newlines(self, isolated_index_service) -> None:
        """Verify proper handling of newline characters."""
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."

        chunks = isolated_index_service._chunk_text(text)

        assert len(chunks) >= 1
        # Content should be preserved
        combined = " ".join(c["text"] for c in chunks)
        assert "Paragraph one" in combined
        assert "Paragraph two" in combined
        assert "Paragraph three" in combined
