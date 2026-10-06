"""
Context-blocks loader and copy assembler for the F2 Supervisor tab (pure).

Loads ``*.md`` template files from a configurable directory (config key
``context_blocks_dir``), parsing a MINIMAL flat YAML frontmatter (``id``,
``name``, ``description`` as ``key: value`` lines — no PyYAML dependency)
plus the markdown body. A missing or unreadable directory degrades to an
empty list with one logged warning. A file WITHOUT valid frontmatter is
never silently dropped (C-7): it loads with ``id`` = filename stem, a
humanized name (dashes → spaces) and the full text as body, with a DEBUG log.

Also provides the assembled-copy format used by the workbench copy buttons:
``N. "quote"`` newline ``: response`` (quote omitted when empty; inner double
quotes escaped, C-5). An entry with no quote AND no response assembles to
``""`` (C-3) so the UI can block the copy with a clear message. All entries
are joined by a blank line in numeric order, empty ones skipped.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

#: Documented default templates directory (config-overridable, ARCH-003).
DEFAULT_CONTEXT_BLOCKS_DIR = r"C:\Dropbox\DOC.RECA\.amBotHs\contextBlocks"

#: Frontmatter delimiters for the minimal flat parser.
_FRONTMATTER_OPEN = "---"
_FLAT_FIELDS = ("id", "name", "description")


@dataclass
class ContextBlock:
    """One insertable context-block template.

    Attributes:
        id: Stable identifier recorded in entries' ``blocks`` lists.
        name: Selectbox label (falls back to ``id``).
        description: Short human description (may be empty).
        body: Markdown text inserted into the response field.
    """

    id: str
    name: str
    description: str = ""
    body: str = ""


def _strip_quotes(value: str) -> str:
    """Strip one pair of surrounding quotes from a frontmatter value.

    Args:
        value: Raw value text after the colon.

    Returns:
        Value without surrounding single/double quotes and whitespace.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1].strip()
    return value


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    """Parse the minimal flat frontmatter of a block file.

    The parser understands ``---`` delimited headers with flat ``key: value``
    lines only (values are split on the FIRST colon; nested YAML is out of
    scope by design — no PyYAML dependency).

    Args:
        text: Full file content.

    Returns:
        ``(fields, body)`` on success; ``None`` when the frontmatter is
        missing or unterminated (caller treats the file as malformed).
    """
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != _FRONTMATTER_OPEN:
        return None
    try:
        closing = next(i for i in range(1, len(lines)) if lines[i].strip() == _FRONTMATTER_OPEN)
    except StopIteration:
        return None
    fields: dict[str, str] = {}
    for raw in lines[1:closing]:
        line = raw.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if key in _FLAT_FIELDS:
            fields[key] = _strip_quotes(value)
    body = "\n".join(lines[closing + 1 :]).strip()
    return fields, body


def load_context_blocks(directory: str | Path) -> list[ContextBlock]:
    """Load every valid ``*.md`` context block from a directory.

    Args:
        directory: Templates directory (config key ``context_blocks_dir``).

    Returns:
        Blocks sorted by name; empty list when the directory is missing,
        unreadable or has no valid block (a warning is logged once for
        missing/unreadable directories and for each malformed file).
    """
    directory = Path(directory)
    if not directory.is_dir():
        logger.warning(
            "Context blocks directory missing or unreadable: %s (using no blocks)",
            directory,
        )
        return []

    blocks: list[ContextBlock] = []
    for path in sorted(directory.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("Context block unreadable, skipping %s: %s", path.name, exc)
            continue
        parsed = _parse_frontmatter(text)
        if parsed is None:
            # C-7: a file without valid frontmatter is still usable — derive
            # its identity from the filename instead of silently dropping it.
            stem = path.stem
            logger.debug(
                "Context block without valid frontmatter, deriving id from filename: %s",
                path.name,
            )
            blocks.append(
                ContextBlock(
                    id=stem, name=stem.replace("-", " "), description="", body=text.strip()
                )
            )
            continue
        fields, body = parsed
        block_id = fields.get("id", "")
        name = fields.get("name", "")
        if not block_id and not name:
            logger.warning("Context block without id/name, skipping: %s", path.name)
            continue
        blocks.append(
            ContextBlock(
                id=block_id or name,
                name=name or block_id,
                description=fields.get("description", ""),
                body=body,
            )
        )
    return sorted(blocks, key=lambda b: b.name.lower())


def assemble_entry(entry) -> str:
    """Assemble one entry into its copy-ready text form.

    Args:
        entry: Object exposing ``number``, ``quote`` and ``response``
            (e.g. :class:`~backend.supervisor_store.SupervisorEntry`).

    Returns:
        ``N. "quote"`` newline ``: response``; when the quote is empty the
        result is just ``N. response``. Inner double quotes of the quote are
        escaped (C-5). When BOTH quote and response are empty/whitespace-only
        the result is ``""`` (C-3) so callers can block empty copies.
    """
    number = int(entry.number)
    quote = str(entry.quote or "").strip()
    response = str(entry.response or "")
    if not quote and not response.strip():
        return ""
    if quote:
        escaped = quote.replace('"', '\\"')
        return f'{number}. "{escaped}"\n: {response}'
    return f"{number}. {response}"


def assemble_all(entries) -> str:
    """Assemble every entry in order, separated by a blank line.

    Args:
        entries: Iterable of entries ordered for copying (numeric order).

    Returns:
        All non-empty assembled entries joined by a blank line (empty ones
        are skipped, C-3); ``""`` when nothing has content.
    """
    parts = [assembled for assembled in (assemble_entry(entry) for entry in entries) if assembled]
    return "\n\n".join(parts)
