"""
Pure file-import helpers for the F1 Files queue.

This module contains NO UI imports and never logs user paths at INFO
(privacy). It provides:

- the documented default audio extension allowlist,
- single-path and batch validation (extension allowlist + existence),
- a soundfile readability probe (extension-valid but undecodable files,
  e.g. WhatsApp OGG/Opus),
- per-file queue status recording and reason localization helpers,
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
from typing import Any

logger = logging.getLogger(__name__)

#: Default audio extension allowlist (no leading dots, lowercase).
DEFAULT_AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {"mp3", "wav", "m4a", "ogg", "flac", "webm", "opus", "aac"}
)

#: Rejection reason: extension not present in the configured allowlist.
REASON_INVALID_TYPE = "invalid_type"

#: Rejection reason: extension allowed but the file does not exist.
REASON_MISSING = "missing"

#: Rejection reason: file exists with an allowed extension but its audio
#: container cannot be opened by soundfile (e.g. WhatsApp OGG/Opus).
REASON_UNREADABLE = "unreadable"

#: Queue failure reason: the transcription service returned no text.
REASON_EMPTY_RESULT = "empty_result"

#: Queue failure reason: the transcription result could not be saved.
REASON_SAVE_FAILED = "save_failed"

#: Queue failure reason: placeholder when no specific cause is known.
REASON_UNKNOWN = "unknown"

#: Stable error reasons that ship a ``files_reason_<reason>`` i18n key.
LOCALIZED_ERROR_REASONS: frozenset[str] = frozenset(
    {REASON_UNREADABLE, REASON_EMPTY_RESULT, REASON_SAVE_FAILED, REASON_UNKNOWN}
)

#: Queue state → ``files_status_*`` i18n key (single source of truth).
FILES_STATUS_KEYS: dict[str, str] = {
    "pending": "files_status_pending",
    "transcribing": "files_status_transcribing",
    "done": "files_status_done",
    "error": "files_status_error",
}


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


def probe_audio_readable(path: str) -> tuple[bool, str]:
    """Probe whether ``path`` opens as readable audio via soundfile.

    Catches files whose extension looks valid but whose container cannot
    be decoded (LT-2: WhatsApp OGG/Opus recordings). Best effort by
    design: when soundfile itself cannot be imported the probe fails OPEN
    so the queue keeps its pre-probe behavior.

    Args:
        path: Filesystem path to an existing audio file.

    Returns:
        Tuple ``(readable, detail)``: ``(True, "")`` when soundfile opens
        the file cleanly, ``(False, "<error summary>")`` otherwise. Never
        raises for string inputs.

    Raises:
        TypeError: If ``path`` is not a string.
    """
    if not isinstance(path, str):
        raise TypeError(f"path must be a string, got {type(path).__name__}")
    if not path:
        return False, "empty path"
    try:
        import soundfile as sf
    except Exception as exc:  # pragma: no cover - soundfile is a hard dependency
        logger.debug("soundfile unavailable; readability probe skipped: %s", exc)
        return True, ""
    try:
        sf.info(path)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return True, ""


def record_file_status(
    status_map: dict[str, tuple[str, str]],
    path: str,
    state: str,
    reason: str | None = None,
) -> tuple[str, str]:
    """Record one per-file queue status with its failure reason.

    Args:
        status_map: Shared per-file status map ``{path: (state, reason)}``.
        path: Queued file path.
        state: Queue state: pending / transcribing / done / error.
        reason: Failure cause; normalized to :data:`REASON_UNKNOWN` for
            errors recorded without one, and to ``""`` for non-errors.

    Returns:
        The recorded ``(state, reason)`` entry.
    """
    entry = (state, (reason or REASON_UNKNOWN) if state == "error" else "")
    status_map[path] = entry
    return entry


def file_reason_text(loc: Any, reason: str) -> str:
    """Map a stable rejection/failure reason to localized user text.

    Args:
        loc: Localization manager exposing ``get_string(key, **kwargs)``.
        reason: Stable technical reason (e.g. ``unreadable``) or free-form
            detail such as an exception summary.

    Returns:
        Localized text when ``reason`` is a known stable reason with a
        translation key; otherwise the raw ``reason`` untouched (free-form
        text is never routed through ``format``).
    """
    if reason in LOCALIZED_ERROR_REASONS:
        text = loc.get_string(f"files_reason_{reason}")
        if not text.startswith("MISSING_TRANSLATION_"):
            return text
    return reason


def file_status_label_text(loc: Any, entry: tuple[str, str]) -> str:
    """Compose the queue label text for one per-file status entry.

    Args:
        loc: Localization manager exposing ``get_string(key, **kwargs)``.
        entry: ``(state, reason)`` pair as stored by
            :func:`record_file_status`.

    Returns:
        Localized state name, plus a parenthesized reason for error
        entries (localized when stable, raw when free-form).
    """
    state, reason = entry
    key = FILES_STATUS_KEYS.get(state)
    text = loc.get_string(key) if key else state
    if state == "error" and reason:
        return f"{text} ({file_reason_text(loc, reason)})"
    return text


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
