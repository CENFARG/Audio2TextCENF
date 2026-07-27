"""@File: audio2text/services/block_loader_service.py
@Description: BlockLoaderService — loads context blocks from Grama's directory
    (YAML frontmatter .md files) and exposes them as BlockMetadata objects.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class LoadedBlock:
    """Metadata and body of a loaded Grama-style block.

    Attributes:
        id: Unique block identifier (from YAML frontmatter).
        name: Human-readable block name.
        description: Short description of the block's purpose.
        hotkey: Optional hotkey binding.
        body: The Markdown body text after the frontmatter.
    """

    id: str
    name: str
    description: str
    hotkey: str
    body: str


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class BlockLoaderService:
    """Loads Grama-style context blocks from .md files.

    Each block file has YAML frontmatter (delimited by ``---``) followed
    by a Markdown body. The service parses these files and returns
    ``LoadedBlock`` instances with metadata and body content.
    """

    def __init__(
        self,
        blocks_dir: Path | str = "C:\\Dropbox\\DOC.RECA\\06-Software\\Grama\\backend\\data\\prompts\\blocks",
    ) -> None:
        """Initialize the block loader.

        Args:
            blocks_dir: Path to the directory containing .md block files.
                        Defaults to Grama's prompts/blocks directory.
        """
        self._blocks_dir = Path(blocks_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_blocks(self) -> list[LoadedBlock]:
        """Load all blocks from the configured directory.

        Scans for ``*.md`` files, parses YAML frontmatter, and returns
        ``LoadedBlock`` instances. Files without valid frontmatter are skipped.

        Returns:
            A list of loaded blocks.
        """
        blocks: list[LoadedBlock] = []

        if not self._blocks_dir.exists():
            return blocks

        for md_file in sorted(self._blocks_dir.glob("*.md")):
            block = self._parse_file(md_file)
            if block:
                blocks.append(block)

        return blocks

    def get_block(self, block_id: str) -> LoadedBlock | None:
        """Retrieve a specific block by ID.

        Args:
            block_id: The block identifier (from YAML frontmatter ``id`` field).

        Returns:
            The LoadedBlock if found, or None.
        """
        target_file = self._blocks_dir / f"{block_id}.md"
        if not target_file.exists():
            return None
        return self._parse_file(target_file)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_file(file_path: Path) -> LoadedBlock | None:
        """Parse a single .md file with YAML frontmatter.

        Args:
            file_path: Path to the .md file.

        Returns:
            A LoadedBlock or None if parsing fails.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

        match = _FRONTMATTER_RE.match(content)
        if not match:
            return None

        try:
            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                return None
        except yaml.YAMLError:
            return None

        body = content[match.end() :].strip()

        return LoadedBlock(
            id=str(frontmatter.get("id", file_path.stem)),
            name=str(frontmatter.get("name", file_path.stem)),
            description=str(frontmatter.get("description", "")),
            hotkey=str(frontmatter.get("hotkey", "")),
            body=body,
        )
