"""
Pure file-import helpers for the F1 Files tab.

This module contains NO UI imports and never logs user paths at INFO
(privacy). It provides:

- the documented default audio extension allowlist,
- single-path and batch validation (extension allowlist + existence),
- tkinterdnd2 drop-data parsing (braced / plain / quoted paths),
- clipboard path extraction: Windows CF_HDROP first (via win32clipboard
  when available), text-path fallback everywhere else.

All rejection reasons are stable technical identifiers, not user-facing
prose: the UI maps them through the localization manager when needed.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable

logger = logging.getLogger(__name__)

#: Default audio extension allowlist (no leading dots, lowercase).
DEFAULT_AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {"mp3", "wav", "m4a", "ogg", "flac", "webm", "opus", "aac"}
)

#: Rejection reason: extension not present in the configured allowlist.
REASON_INVALID_TYPE = "invalid_type"

#: Rejection reason: extension allowed but the file does not exist.
REASON_MISSING = "missing"


def _normalize_extensions(extensions: Iterable[str] | None) -> frozenset[str]:
    """Normalize an extension iterable to a lowercase dot-free frozenset.

    Args:
        extensions: Extension candidates such as ``mp3`` or ``.mp3``.
            ``None`` selects :data:`DEFAULT_AUDIO_EXTENSIONS`.

    Returns:
        Normalized extension set used for allowlist comparisons.
    """
    if extensions is None:
        return DEFAULT_AUDIO_EXTENSIONS
    return frozenset(str(ext).strip().lstrip(".").lower() for ext in extensions if str(ext).strip())


def is_audio_file(path: str, extensions: Iterable[str] | None = None) -> bool:
    """Check whether ``path`` is an existing file with an allowed extension.

    Args:
        path: Candidate filesystem path. Must be a non-empty string.
        extensions: Extension allowlist; ``None`` uses the documented
            default allowlist.

    Returns:
        True only when the path has an allowed extension AND exists.

    Raises:
        TypeError: If ``path`` is not a string.
    """
    if not isinstance(path, str):
        raise TypeError(f"path must be a string, got {type(path).__name__}")
    if not path:
        return False
    allowed = _normalize_extensions(extensions)
    suffix = os.path.splitext(path)[1].lstrip(".").lower()
    if not suffix or suffix not in allowed:
        return False
    return os.path.isfile(path)


def filter_audio_paths(
    paths: Iterable[str] | None,
    extensions: Iterable[str] | None = None,
) -> tuple[list[str], list[tuple[str, str]]]:
    """Split candidate paths into accepted files and rejected entries.

    Every candidate is validated against the extension allowlist and an
    existence check. Duplicates (case-insensitive) within the batch are
    silently ignored, matching the queue de-duplication requirement.

    Args:
        paths: Candidate paths; surrounding whitespace and quotes are
            stripped. ``None`` is treated as an empty batch.
        extensions: Extension allowlist; ``None`` uses the default.

    Returns:
        A tuple ``(accepted, rejected)`` where ``accepted`` is the list of
        valid unique paths in input order and ``rejected`` maps each
        invalid entry to a stable reason: ``invalid_type`` (extension not
        allowed) or ``missing`` (allowed extension, file absent).
    """
    allowed = _normalize_extensions(extensions)
    accepted: list[str] = []
    rejected: list[tuple[str, str]] = []
    seen = set()
    for raw in paths or []:
        path = str(raw).strip().strip("\"'")
        if not path:
            continue
        key = os.path.normcase(path).lower()
        if key in seen:
            continue
        seen.add(key)
        suffix = os.path.splitext(path)[1].lstrip(".").lower()
        if not suffix or suffix not in allowed:
            rejected.append((path, REASON_INVALID_TYPE))
        elif not os.path.isfile(path):
            rejected.append((path, REASON_MISSING))
        else:
            accepted.append(path)
    return accepted, rejected


def split_drop_data(data: str) -> list[str]:
    """Parse a tkinterdnd2 ``<<Drop>>`` ``event.data`` string into paths.

    Paths containing spaces arrive wrapped in braces (``{C:/my dir/a.mp3}``);
    plain paths are space separated. Surrounding quotes are stripped.

    Args:
        data: Raw drop data string.

    Returns:
        Extracted path strings, in order of appearance.
    """
    if not data:
        return []
    paths: list[str] = []
    token: list[str] = []
    in_braces = False
    in_quotes = False
    for char in data:
        if char == "{":
            in_braces = True
        elif char == "}":
            in_braces = False
        elif char == '"':
            in_quotes = not in_quotes
        elif char == " " and not in_braces and not in_quotes:
            candidate = "".join(token).strip()
            if candidate:
                paths.append(candidate)
            token = []
        else:
            token.append(char)
    tail = "".join(token).strip()
    if tail:
        paths.append(tail)
    return [p.strip("\"'") for p in paths if p.strip("\"'")]


def paths_from_clipboard_text(text: str) -> list[str]:
    """Extract existing file paths from clipboard text, one per line.

    Lines are stripped of whitespace and surrounding quotes, user home
    (``~``) is expanded, and only paths pointing to existing files are
    kept.

    Args:
        text: Raw clipboard text; may be empty.

    Returns:
        Existing file paths, in order of appearance.
    """
    if not text:
        return []
    paths: list[str] = []
    for raw_line in text.splitlines():
        candidate = raw_line.strip().strip("\"'")
        if not candidate:
            continue
        candidate = os.path.expanduser(candidate)
        if os.path.isfile(candidate):
            paths.append(candidate)
    return paths


def _read_clipboard_hdrop() -> list[str]:
    """Read the CF_HDROP file list from the Windows clipboard, best effort.

    Uses ``win32clipboard`` when importable. Any failure (missing pywin32,
    non-Windows platform, clipboard locked by another process) results in
    an empty list and a DEBUG log entry.

    Returns:
        File paths currently on the clipboard as CF_HDROP, possibly empty.
    """
    try:
        import win32clipboard  # type: ignore[import-not-found]
    except ImportError:
        return []
    try:
        win32clipboard.OpenClipboard()
        try:
            if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                return []
            data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
        finally:
            win32clipboard.CloseClipboard()
        return [str(item) for item in (data or [])]
    except Exception as exc:  # clipboard access can fail for many reasons
        logger.debug("CF_HDROP clipboard read failed: %s", exc)
        return []


def _read_clipboard_text() -> str:
    """Read raw clipboard text via pyperclip, best effort.

    Returns:
        Clipboard text, or an empty string when unavailable (headless
        environments, no paste mechanism, etc.).
    """
    try:
        import pyperclip

        return pyperclip.paste() or ""
    except Exception as exc:
        logger.debug("Clipboard text read failed: %s", exc)
        return ""


def paths_from_clipboard() -> list[str]:
    """Extract file paths from the clipboard.

    Windows CF_HDROP (files copied in the OS shell) is preferred; when it
    yields nothing, the text content is parsed as one path per line.

    Returns:
        Existing file paths from whichever source produced results.
    """
    paths = _read_clipboard_hdrop()
    if paths:
        return paths
    return paths_from_clipboard_text(_read_clipboard_text())
