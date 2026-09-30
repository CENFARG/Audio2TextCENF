"""
Unit tests for the F2 context-blocks loader and copy assembler (pure module).

Covers the openspec audio2text-f2-supervisor context-blocks contract:
- minimal flat YAML frontmatter parsing (no PyYAML dependency)
- body extraction after the closing ``---``
- missing / unreadable directory degrades to [] with one warning
- malformed files are skipped (no frontmatter, unterminated frontmatter,
  no id/name), never fatal
- assemble_entry: ``N. "quote"`` + newline + ``: response`` (quote omitted
  when empty); assemble_all: blank-line separation, numeric order
"""

import logging
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.context_blocks import DEFAULT_CONTEXT_BLOCKS_DIR
from backend.context_blocks import ContextBlock
from backend.context_blocks import assemble_all
from backend.context_blocks import assemble_entry
from backend.context_blocks import load_context_blocks


def _write_block(directory: Path, name: str, content: str) -> Path:
    """Write a ``.md`` block file into ``directory`` and return its path."""
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.unit
class TestFrontmatterParsing:
    """Flat frontmatter parse + body extraction."""

    def test_parses_flat_frontmatter_fields_and_body(self, tmp_path):
        # Arrange
        _write_block(
            tmp_path,
            "one.md",
            "---\nid: tone\nname: Tono directo\ndescription: Correcciones de tono\n---\n"
            "Usá tono directo.\n\nSegundo párrafo.\n",
        )

        # Act
        blocks = load_context_blocks(tmp_path)

        # Assert
        assert len(blocks) == 1
        block = blocks[0]
        assert isinstance(block, ContextBlock)
        assert (block.id, block.name, block.description) == (
            "tone",
            "Tono directo",
            "Correcciones de tono",
        )
        assert block.body == "Usá tono directo.\n\nSegundo párrafo."

    def test_name_falls_back_to_id_and_vice_versa(self, tmp_path):
        # Arrange: one block without name, one without id
        _write_block(tmp_path, "a.md", "---\nid: solo-id\n---\nBody A")
        _write_block(tmp_path, "b.md", "---\nname: Solo Nombre\n---\nBody B")

        # Act
        blocks = load_context_blocks(tmp_path)

        # Assert
        by_id = {b.id: b for b in blocks}
        assert by_id["solo-id"].name == "solo-id"
        assert by_id["Solo Nombre"].body == "Body B"

    def test_blocks_sorted_by_name(self, tmp_path):
        # Arrange: files created out of name order
        _write_block(tmp_path, "z.md", "---\nid: zulu\nname: Zulu\n---\nZ")
        _write_block(tmp_path, "a.md", "---\nid: alpha\nname: Alpha\n---\nA")
        _write_block(tmp_path, "m.md", "---\nid: mike\nname: Mike\n---\nM")

        # Act
        blocks = load_context_blocks(tmp_path)

        # Assert
        assert [b.name for b in blocks] == ["Alpha", "Mike", "Zulu"]

    def test_values_with_colons_and_quotes_parse(self, tmp_path):
        # Arrange: description contains a colon and quoted value
        _write_block(
            tmp_path,
            "c.md",
            '---\nid: colon\nname: "Con: dos puntos"\ndescription: usa: dos puntos\n---\nB',
        )

        # Act
        blocks = load_context_blocks(tmp_path)

        # Assert: split on FIRST colon only, surrounding quotes stripped
        assert blocks[0].name == "Con: dos puntos"
        assert blocks[0].description == "usa: dos puntos"


@pytest.mark.unit
class TestDirectoryDegradation:
    """Missing / unreadable dir -> [] with a logged warning (never crash)."""

    def test_missing_directory_returns_empty_with_warning(self, tmp_path, caplog):
        # Act
        with caplog.at_level(logging.WARNING, logger="backend.context_blocks"):
            blocks = load_context_blocks(tmp_path / "does-not-exist")

        # Assert
        assert blocks == []
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_directory_path_that_is_a_file_returns_empty_with_warning(self, tmp_path, caplog):
        # Arrange: path exists but is a file, not a directory
        file_path = tmp_path / "not-a-dir"
        file_path.write_text("x", encoding="utf-8")

        # Act
        with caplog.at_level(logging.WARNING, logger="backend.context_blocks"):
            blocks = load_context_blocks(file_path)

        # Assert
        assert blocks == []
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_empty_directory_returns_empty_list(self, tmp_path):
        # Act / Assert: valid but empty -> [] (no warning required)
        assert load_context_blocks(tmp_path) == []

    def test_non_md_files_are_ignored(self, tmp_path):
        # Arrange
        _write_block(tmp_path, "notes.txt", "---\nid: t\nname: T\n---\nbody")
        (tmp_path / "sub.json").write_text("{}", encoding="utf-8")

        # Act / Assert
        assert load_context_blocks(tmp_path) == []


@pytest.mark.unit
class TestMalformedFiles:
    """Malformed block files are skipped with a warning, never fatal."""

    def test_file_without_frontmatter_is_skipped(self, tmp_path, caplog):
        # Arrange
        _write_block(tmp_path, "bad.md", "just text, no frontmatter\n")

        # Act
        with caplog.at_level(logging.WARNING, logger="backend.context_blocks"):
            blocks = load_context_blocks(tmp_path)

        # Assert
        assert blocks == []
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_unterminated_frontmatter_is_skipped(self, tmp_path):
        # Arrange: opening --- but no closing ---
        _write_block(tmp_path, "bad.md", "---\nid: x\nname: X\nbody without closing")

        # Act / Assert
        assert load_context_blocks(tmp_path) == []

    def test_block_without_id_and_name_is_skipped(self, tmp_path):
        # Arrange
        _write_block(tmp_path, "bad.md", "---\ndescription: no identity\n---\nBody")

        # Act / Assert
        assert load_context_blocks(tmp_path) == []

    def test_good_blocks_survive_malformed_siblings(self, tmp_path):
        # Arrange
        _write_block(tmp_path, "bad.md", "no frontmatter")
        _write_block(tmp_path, "good.md", "---\nid: ok\nname: Ok\n---\nBody")

        # Act
        blocks = load_context_blocks(tmp_path)

        # Assert
        assert [b.id for b in blocks] == ["ok"]


@pytest.mark.unit
class TestAssembleEntry:
    """Assembled copy format: N. "quote" \\n : response."""

    def test_assemble_entry_with_quote(self):
        # Arrange
        entry = SimpleNamespace(number=3, quote="la IA dijo esto", response="corrección")

        # Act / Assert
        assert assemble_entry(entry) == '3. "la IA dijo esto"\n: corrección'

    def test_assemble_entry_without_quote_omits_quote_line(self):
        # Arrange
        entry = SimpleNamespace(number=1, quote="", response="solo corrección")

        # Act / Assert
        assert assemble_entry(entry) == "1. solo corrección"

    def test_assemble_all_joins_with_blank_line_in_order(self):
        # Arrange
        entries = [
            SimpleNamespace(number=1, quote="q1", response="r1"),
            SimpleNamespace(number=2, quote="", response="r2"),
        ]

        # Act
        result = assemble_all(entries)

        # Assert: blank line between assembled entries
        assert result == '1. "q1"\n: r1\n\n2. r2'

    def test_assemble_all_empty(self):
        # Act / Assert
        assert assemble_all([]) == ""


@pytest.mark.unit
class TestModuleSurface:
    """Documented default dir exists and dataclass shape is stable."""

    def test_default_context_blocks_dir_is_configured_path(self):
        # Assert: documented default (config-overridable, ARCH-003)
        assert "contextBlocks" in DEFAULT_CONTEXT_BLOCKS_DIR
