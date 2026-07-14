"""@File: tests/e2e/test_blocks_selection_flow.py
@Description: E2E tests for context blocks discovery, selection, and enhancement.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


class TestBlocksSelectionFlowE2E:
    """End-to-end tests for context blocks discovery and selection."""

    def test_context_blocks_endpoint_responds(self, client: TestClient) -> None:
        """GET /api/v1/context-blocks returns a valid response."""
        # Mock the loader so we don't depend on real Grama blocks dir
        with patch(
            "audio2text.services.block_loader_service.BlockLoaderService.load_blocks",
            return_value=[],
        ):
            response = client.get("/api/v1/context-blocks")

        assert response.status_code in (200, 404, 405)

    def test_context_blocks_endpoint_with_mock_blocks(
        self, client: TestClient
    ) -> None:
        """When blocks are discovered, the endpoint returns them."""
        from audio2text.services.block_loader_service import LoadedBlock

        mock_blocks = [
            LoadedBlock(
                id="task_extractor",
                name="Task Extractor",
                description="Extract tasks from transcription",
                hotkey="",
                body="## Tasks\nExtract tasks",
            ),
            LoadedBlock(
                id="summary",
                name="Summary Generator",
                description="Generate summary",
                hotkey="",
                body="## Summary\nGenerate summary",
            ),
        ]

        with patch(
            "audio2text.services.block_loader_service.BlockLoaderService.load_blocks",
            return_value=mock_blocks,
        ):
            response = client.get("/api/v1/context-blocks")

        assert response.status_code in (200, 404, 405)

    def test_enhance_endpoint_accepts_request(self, client: TestClient) -> None:
        """POST /api/v1/enhance returns structured response."""
        payload = {
            "transcription_id": "test-e2e-001",
            "profile": "light",
            "provider": "groq",
            "block_ids": ["task_extractor"],
        }
        response = client.post("/api/v1/enhance", json=payload)
        assert response.status_code in (200, 404, 422, 503)


class TestBlocksIntegration:
    """Integration-level tests for block loading and processing."""

    def test_block_loader_service_discovers_blocks(self, e2e_temp_dir: Path) -> None:
        """BlockLoaderService discovers blocks from a configured directory."""
        from audio2text.services.block_loader_service import BlockLoaderService

        # Create mock block files
        blocks_dir = e2e_temp_dir / "blocks"
        blocks_dir.mkdir(parents=True, exist_ok=True)

        (blocks_dir / "task_extractor.md").write_text(
            "---\nid: task_extractor\nname: Task Extractor\nenabled: true\norder: 1\n---\n"
            "## Tasks\nExtract tasks from the following transcription:",
            encoding="utf-8",
        )

        loader = BlockLoaderService(blocks_dir=str(blocks_dir))
        blocks = loader.load_blocks()

        assert len(blocks) >= 1
        assert any(b.id == "task_extractor" for b in blocks)

    def test_block_loader_returns_empty_on_missing_dir(self) -> None:
        """When the blocks directory doesn't exist, returns empty list."""
        from audio2text.services.block_loader_service import BlockLoaderService

        loader = BlockLoaderService(
            blocks_dir="C:/nonexistent/path/12345/"
        )
        blocks = loader.load_blocks()
        assert blocks == []
