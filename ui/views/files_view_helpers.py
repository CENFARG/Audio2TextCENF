"""
Files view helpers — pure status/label glue + queue worker mixin.

Extracted from ``ui/views/files_view.py`` (behavior-preserving split, files
≤400 lines rule): the localized status/label/reason helpers (C-4), the
headless DesignSystem fallback palette and the sequential transcription
worker with its status-recording choke points. Section construction,
import sources and queue UI stay in :mod:`ui.views.files_view`.
"""

from __future__ import annotations

from ui.theme import DesignSystem

import logging
import os
import threading
from typing import Any

from backend import file_import

logger = logging.getLogger(__name__)


def queue_reason_display_text(loc: Any, reason: str) -> str:
    """Localized reason text for a queue row, extending the backend map (C-4).

    ``backend/file_import.py`` is a frozen surface for this view, so the
    extra stable reason ``missing`` is translated here; every other reason
    delegates to :func:`backend.file_import.file_reason_text` untouched.

    Args:
        loc: Localization manager exposing ``get_string(key, **kwargs)``.
        reason: Stable technical reason (e.g. ``missing``) or free-form text.

    Returns:
        Localized text when the reason is known, otherwise the raw reason.
    """
    if reason == file_import.REASON_MISSING:
        text = loc.get_string("files_reason_missing")
        if not str(text).startswith("MISSING_TRANSLATION_"):
            return str(text)
    return file_import.file_reason_text(loc, reason)


def queue_status_label_text(loc: Any, entry: tuple[str, str]) -> str:
    """Compose the queue row label for one ``(state, reason)`` pair (C-4).

    Mirrors :func:`backend.file_import.file_status_label_text` but routes
    the reason through :func:`queue_reason_display_text` so a vanished
    source file shows ``Error (Archivo no encontrado)`` instead of the raw
    ``missing`` id.

    Args:
        loc: Localization manager exposing ``get_string(key, **kwargs)``.
        entry: ``(state, reason)`` pair as stored by
            :func:`backend.file_import.record_file_status`.

    Returns:
        Localized state name, plus a parenthesized reason for error entries.
    """
    state, reason = entry
    key = file_import.FILES_STATUS_KEYS.get(state)
    text = loc.get_string(key) if key else state
    if state == "error" and reason:
        return f"{text} ({queue_reason_display_text(loc, reason)})"
    return text


def build_combined_output(results: list[tuple[str, str]]) -> str:
    """Compose the combined queue output with flat separators (S9).

    A single file returns its text untouched (no header noise for the
    common single-file paste); several files are joined as
    ``=== basename ===`` blocks in queue order, separated by a blank line.

    Args:
        results: ``(basename, transcription)`` pairs in queue order for
            the files that transcribed successfully.

    Returns:
        The combined text ready for the panel and the clipboard, or an
        empty string when no file succeeded.
    """
    if not results:
        return ""
    if len(results) == 1:
        return results[0][1]
    return "\n\n".join(f"=== {name} ===\n{text}" for name, text in results)


def load_design_system():
    """Resolve the theme ``DesignSystem`` facade (prototype palette)."""

    return DesignSystem


class FilesQueueWorkerMixin:
    """Mixin running the single sequential transcription worker thread."""

    # Host attributes (HC-02 mixin pattern; provided by ui.app.App at runtime).
    localization_manager: Any
    config_manager: Any
    transcriber: Any
    file_manager: Any
    sound_manager: Any
    after: Any
    update_status: Any
    display_transcription: Any
    # Queue state owned by FilesViewMixin._ensure_files_queue_state.
    _files_queue: list[str]
    _files_status: dict[str, tuple[str, str]]
    _files_worker_running: bool
    _files_worker_lock: threading.Lock
    _files_texts: dict[str, str]
    # UI-side status renderer defined on FilesViewMixin (the host).
    _set_file_status: Any

    # ── Sequential worker (exactly one thread at a time) ────
    def _files_queue_worker(self) -> None:
        """Iterate the queue sequentially until no pending file remains.

        S9: every successful transcription is collected and ONE combined
        display is scheduled at the end (panel + clipboard + auto-paste
        receive the whole block with ``=== name ===`` separators) instead
        of each file overwriting the previous one.
        """
        pending_count = len(self._files_queue)
        logger.info("Files queue worker started (%d pending)", pending_count)
        done_count = 0
        results: list[tuple[str, str]] = []
        while True:
            path = self._next_pending_file()
            if path is None:
                break
            if self._process_one_file(path):
                done_count += 1
                text = self._files_texts.pop(path, "")
                results.append((os.path.basename(path), text))
        combined = build_combined_output(results)
        if combined:
            self.after(0, self.display_transcription, combined)
        with self._files_worker_lock:
            self._files_worker_running = False
        self.after(0, self._files_queue_finished, done_count)

    def _next_pending_file(self) -> str | None:
        """Return the next pending path in queue order, or ``None``.

        Returns:
            The first queued path still marked pending, if any.
        """
        with self._files_worker_lock:
            for path in self._files_queue:
                if (self._files_status.get(path) or ("", ""))[0] == "pending":
                    return path
        return None

    def _process_one_file(self, path: str) -> bool:
        """Transcribe one file through the existing retranscription flow.

        Mirrors ``App._retranscribe_thread``: transcribe_with_groq →
        display_transcription → save_transcription_entry (same entry keys).
        UI updates are scheduled on the main thread; a failure marks only
        this file as error (with its reason, via ``_mark_file_error``) and
        never stops the queue.

        Args:
            path: Audio file path to transcribe.

        Returns:
            True when the file was transcribed and saved successfully.
        """
        if not os.path.exists(path):
            # C-4: a vanished source must fail fast with a specific localized
            # reason — no Groq call, no generic "Fallo en la transcripción".
            self._mark_file_error(path, file_import.REASON_MISSING)
            return False
        self._set_file_state_threadsafe(path, "transcribing")
        try:
            text = self.transcriber.transcribe_with_groq(path)
        except Exception as exc:
            self._mark_file_error(path, f"{type(exc).__name__}: {exc}")
            return False
        if not text:
            self._mark_file_error(path, file_import.REASON_EMPTY_RESULT)
            return False
        try:
            self._files_texts[path] = text
            self.file_manager.save_transcription_entry(
                {
                    "text": text,
                    "duration": 0,  # Duration unknown/irrelevant for file import
                    "language": self.config_manager.get(
                        "transcription_language",
                        self.config_manager.get("default_language", "es"),
                    ),
                    "audio_file": path,
                }
            )
        except Exception as exc:
            logger.debug("Save failure detail for %s: %s", path, exc)
            self._mark_file_error(path, file_import.REASON_SAVE_FAILED)
            return False
        self._set_file_state_threadsafe(path, "done")
        return True

    def _files_queue_finished(self, done_count: int) -> None:
        """Report the queue outcome on the main thread (status bar + sound).

        Args:
            done_count: Number of files transcribed successfully.
        """
        loc = self.localization_manager
        if done_count > 0:
            self.update_status(loc.get_string("transcription_completed"), "green")
            self.sound_manager.sound_success()
        else:
            self.update_status(loc.get_string("transcription_failed"), "red")
        logger.info("Files queue finished (%d succeeded)", done_count)

    def _set_file_state_threadsafe(self, path: str, state: str) -> None:
        """Record a non-error state change from any thread; schedule the UI.

        Args:
            path: Queued file path.
            state: One of pending / transcribing / done.
        """
        entry = file_import.record_file_status(self._files_status, path, state)
        self.after(0, self._set_file_status, path, entry)

    def _mark_file_error(self, path: str, reason: str) -> None:
        """Mark one file failed: record the reason, log ONE ERROR, update UI.

        Single choke point for every queue failure so each failed file
        produces exactly one clear ERROR log line carrying its reason
        (LT-4 observability).

        Args:
            path: Queued file path.
            reason: Stable reason id or free-form exception summary.
        """
        entry = file_import.record_file_status(
            self._files_status, path, "error", reason
        )
        logger.error("Queued file failed (%s): %s", entry[1], path)
        self.after(0, self._set_file_status, path, entry)
