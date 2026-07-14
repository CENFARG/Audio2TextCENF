"""@File: tests/unit/test_block_loader_service.py
@Description: Unit tests for BlockLoaderService (Task 3.4b). TDD cycle.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import tempfile
from pathlib import Path


class TestBlockLoaderServiceInit:
    """Tests for BlockLoaderService initialization."""

    def test_create_with_blocks_dir(self) -> None:
        """Service can be created with a blocks directory."""
        from audio2text.services.block_loader_service import BlockLoaderService

        with tempfile.TemporaryDirectory() as tmp:
            service = BlockLoaderService(blocks_dir=Path(tmp))
            assert service is not None


class TestBlockLoaderServiceLoad:
    """Tests for loading blocks from .md files with YAML frontmatter."""

    def test_load_single_block(self) -> None:
        """load_blocks() parses a .md file with YAML frontmatter."""
        from audio2text.services.block_loader_service import BlockLoaderService

        with tempfile.TemporaryDirectory() as tmp:
            blocks_dir = Path(tmp)
            # Write a sample Grama-style block file
            content = """---
id: test_block
name: Test Block
description: A block for testing.
hotkey: "ctrl+t"
---
### Test Block Content
This is the body of the block.
"""
            (blocks_dir / "test.md").write_text(content, encoding="utf-8")

            service = BlockLoaderService(blocks_dir=blocks_dir)
            blocks = service.load_blocks()

            assert len(blocks) == 1
            assert blocks[0].id == "test_block"
            assert blocks[0].name == "Test Block"

    def test_load_multiple_blocks(self) -> None:
        """load_blocks() finds all .md files in the directory."""
        from audio2text.services.block_loader_service import BlockLoaderService

        with tempfile.TemporaryDirectory() as tmp:
            blocks_dir = Path(tmp)
            (blocks_dir / "a.md").write_text(
                "---\nid: a\nname: Block A\ndescription: First\nhotkey: ''\n---\nBody A\n",
                encoding="utf-8",
            )
            (blocks_dir / "b.md").write_text(
                "---\nid: b\nname: Block B\ndescription: Second\nhotkey: 'alt+b'\n---\nBody B\n",
                encoding="utf-8",
            )

            service = BlockLoaderService(blocks_dir=blocks_dir)
            blocks = service.load_blocks()

            assert len(blocks) == 2

    def test_load_returns_body_content(self) -> None:
        """Loaded blocks include the body text after frontmatter."""
        from audio2text.services.block_loader_service import BlockLoaderService

        with tempfile.TemporaryDirectory() as tmp:
            blocks_dir = Path(tmp)
            (blocks_dir / "c.md").write_text(
                "---\nid: c\nname: Block C\ndescription: Test\nhotkey: ''\n---\nThis is body content.\nMore lines.\n",
                encoding="utf-8",
            )

            service = BlockLoaderService(blocks_dir=blocks_dir)
            blocks = service.load_blocks()

            assert "This is body content." in blocks[0].body

    def test_load_empty_directory(self) -> None:
        """Loading from an empty directory returns empty list."""
        from audio2text.services.block_loader_service import BlockLoaderService

        with tempfile.TemporaryDirectory() as tmp:
            service = BlockLoaderService(blocks_dir=Path(tmp))
            blocks = service.load_blocks()

            assert blocks == []

    def test_get_block_by_id(self) -> None:
        """get_block() retrieves a specific block by ID."""
        from audio2text.services.block_loader_service import BlockLoaderService

        with tempfile.TemporaryDirectory() as tmp:
            blocks_dir = Path(tmp)
            (blocks_dir / "findme.md").write_text(
                "---\nid: findme\nname: Find Me\ndescription: Search test\nhotkey: ''\n---\nBody\n",
                encoding="utf-8",
            )

            service = BlockLoaderService(blocks_dir=blocks_dir)
            block = service.get_block("findme")

            assert block is not None
            assert block.id == "findme"

    def test_get_nonexistent_block_returns_none(self) -> None:
        """get_block() returns None for nonexistent ID."""
        from audio2text.services.block_loader_service import BlockLoaderService

        with tempfile.TemporaryDirectory() as tmp:
            service = BlockLoaderService(blocks_dir=Path(tmp))
            assert service.get_block("nope") is None
