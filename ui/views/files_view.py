"""
FilesViewMixin — queue UI + sequential transcription worker for the F1 Files tab.

Builds the Files tab (action buttons, pending queue, drop hint, rejection
report) and runs a SINGLE worker thread transcribing queued files one at a
time, reusing the proven retranscription flow (transcribe_with_groq →
display_transcription → save_transcription_entry). Per-file status lives in
``{path: status}`` (pending / transcribing / done / error); a failed file is
marked error and the queue continues. Worker → UI updates are scheduled via
``self.after``. API contract: App inherits this mixin (HC-02 mixin pattern).
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Iterable
from tkinter import filedialog

from backend import file_import
from backend.file_import import DEFAULT_AUDIO_EXTENSIONS, filter_audio_paths

logger = logging.getLogger(__name__)

try:  # availability flag for drop-target registration (degrades gracefully)
    from tkinterdnd2 import DND_FILES  # type: ignore  # noqa: F401

    _TKDND_AVAILABLE = True
except ImportError:  # distributed builds may not ship tkdnd
    DND_FILES = "<<Drop>>"  # placeholder; never registered when unavailable
    _TKDND_AVAILABLE = False


class FilesViewMixin:
    """Mixin providing the Files tab: import sources + sequential queue."""

    #: per-status i18n keys
    _STATUS_KEYS = {
        "pending": "files_status_pending",
        "transcribing": "files_status_transcribing",
        "done": "files_status_done",
        "error": "files_status_error",
    }

    #: status → DesignSystem color (fallbacks match ui.app palette)
    _STATUS_COLORS = {
        "pending": "#CBD5E1",
        "transcribing": "#F59E0B",
        "done": "#10B981",
        "error": "#EF4444",
    }

    # ── Tab construction ──────────────────────────────────────────
    def create_files_tab(self) -> None:
        """Build the Files tab: actions row, pending queue and drop hint."""
        import customtkinter as ctk

        try:
            from ui.app import DesignSystem  # type: ignore[assignment]
        except ImportError:  # pragma: no cover - direct-run convenience

            class DesignSystem:  # type: ignore[no-redef]
                """Fallback palette matching ui.app.DesignSystem."""

                COLORS = {
                    "primary": "#2563EB",
                    "primary_hover": "#1D4ED8",
                    "warning": "#F59E0B",
                    "text_secondary": "#CBD5E1",
                }
                TYPOGRAPHY = {
                    "heading_medium": ("Segoe UI", 16, "bold"),
                    "body_medium": ("Segoe UI", 14, "normal"),
                    "body_small": ("Segoe UI", 12, "normal"),
                }

        self._ensure_files_queue_state()
        loc = self.localization_manager
        tab = self.main_frame.tab(loc.get_string("tab_files"))
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="ew")
        ctk.CTkLabel(
            header,
            text=loc.get_string("files_title"),
            font=DesignSystem.TYPOGRAPHY["heading_medium"],
        ).pack(side="left")

        actions = ctk.CTkFrame(tab, fg_color="transparent")
        actions.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(
            actions,
            text=loc.get_string("files_load"),
            width=130,
            command=self._load_files_via_dialog,
        ).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            actions,
            text=loc.get_string("files_paste"),
            width=130,
            command=self.add_files_from_clipboard,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            actions,
            text=loc.get_string("files_transcribe"),
            width=150,
            fg_color=DesignSystem.COLORS["primary"],
            hover_color=DesignSystem.COLORS["primary_hover"],
            command=self.transcribe_all_queue,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            actions,
            text=loc.get_string("files_clear"),
            width=90,
            fg_color="transparent",
            border_width=1,
            command=self.clear_files_queue,
        ).pack(side="right")

        self.files_rejected_label = ctk.CTkLabel(
            tab,
            text="",
            justify="left",
            anchor="w",
            wraplength=520,
            font=DesignSystem.TYPOGRAPHY["body_small"],
            text_color=DesignSystem.COLORS["warning"],
        )
        self.files_rejected_label.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="ew")

        self.files_queue_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.files_queue_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        if self._dnd_available and _TKDND_AVAILABLE:
            self.files_drop_hint = ctk.CTkLabel(
                self.files_queue_frame,
                text=loc.get_string("files_drop_hint"),
                font=DesignSystem.TYPOGRAPHY["body_medium"],
                text_color=DesignSystem.COLORS["text_secondary"],
            )
            self.files_drop_hint.pack(pady=30, fill="x", expand=True)

    # ── Queue state ───────────────────────────────────────────────
    def _ensure_files_queue_state(self) -> None:
        """Initialize queue state once (idempotent, before any enqueue)."""
        if hasattr(self, "_files_queue"):
            return
        self._files_queue: list[str] = []
        self._files_status: dict[str, str] = {}
        self._files_status_labels: dict[str, object] = {}
        self._files_worker_running = False
        self._files_worker_lock = threading.Lock()

    def _files_extensions(self) -> frozenset[str]:
        """Return the configured import allowlist or the documented default."""
        configured = getattr(self, "audio_import_extensions", None)
        return frozenset(configured) if configured else DEFAULT_AUDIO_EXTENSIONS

    # ── Import sources ────────────────────────────────────────────
    def add_files_to_queue(self, paths: Iterable[str]) -> tuple[list[str], list[tuple[str, str]]]:
        """Validate candidates and append new ones to the pending queue.

        Returns:
            Tuple ``(added, rejected)``: newly enqueued paths and rejected
            ``(path, reason)`` entries.
        """
        self._ensure_files_queue_state()
        accepted, rejected = filter_audio_paths(paths, self._files_extensions())
        already = {os.path.normcase(p) for p in self._files_queue}
        added = [p for p in accepted if os.path.normcase(p) not in already]
        for path in added:
            self._files_queue.append(path)
            self._files_status[path] = "pending"
        if added or rejected:
            self.after(0, self._append_queue_rows, added, rejected)
        if rejected:
            logger.info("Rejected %d invalid file(s) from import", len(rejected))
        return added, rejected

    def add_files_from_clipboard(self) -> None:
        """Read file paths from the clipboard and enqueue them."""
        try:
            paths = file_import.paths_from_clipboard()
        except Exception as exc:
            logger.error("Clipboard path extraction failed: %s", exc)
            return
        if paths:
            self.add_files_to_queue(paths)

    def _on_files_drop(self, event) -> str:
        """Handle a tkinterdnd2 ``<<Drop>>`` event on the window.

        Args:
            event: Tk event whose ``data`` holds the dropped paths.

        Returns:
            ``"break"`` to stop event propagation.
        """
        if self.main_frame.get() != self.localization_manager.get_string("tab_files"):
            return "break"
        self.add_files_to_queue(file_import.split_drop_data(event.data))
        return "break"

    def _on_files_paste_hotkey(self, event=None) -> str | None:
        """Ctrl-V handler: paste paths only while the Files tab is active.

        Args:
            event: Tk key event (unused).

        Returns:
            ``"break"`` when handled, ``None`` to let default paste proceed.
        """
        if self.main_frame.get() != self.localization_manager.get_string("tab_files"):
            return None
        self.add_files_from_clipboard()
        return "break"

    def _load_files_via_dialog(self) -> None:
        """Open a multi-select file dialog and enqueue the chosen audio files."""
        patterns = " ".join(f"*.{ext}" for ext in sorted(self._files_extensions()))
        loc = self.localization_manager
        paths = filedialog.askopenfilenames(
            title=loc.get_string("files_title"),
            filetypes=[
                (loc.get_string("files_filetype_audio"), patterns),
                (loc.get_string("files_filetype_all"), "*.*"),
            ],
        )
        if paths:
            self.add_files_to_queue(paths)

    # ── Queue UI (main thread) ────────────────────────────────
    def _append_queue_rows(self, added: list[str], rejected: list[tuple[str, str]]) -> None:
        """Render new queue rows and the rejection report.

        Args:
            added: Paths newly enqueued (a row is created per path).
            rejected: ``(path, reason)`` pairs to report to the user.
        """
        import customtkinter as ctk

        hint = getattr(self, "files_drop_hint", None)
        if hint is not None and hint.winfo_exists():
            hint.destroy()
        for path in added:
            row = ctk.CTkFrame(self.files_queue_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                row,
                text=os.path.basename(path),
                anchor="w",
                font=("Segoe UI", 12),
            ).pack(side="left", padx=(5, 10))
            status_label = ctk.CTkLabel(row, text="", anchor="e")
            status_label.pack(side="right", padx=5)
            self._files_status_labels[path] = status_label
            self._set_file_status(path, self._files_status.get(path, "pending"))
        self._show_rejected(rejected)

    def _show_rejected(self, rejected: list[tuple[str, str]]) -> None:
        """Render rejected entries (per-entry reason) in the report label.

        Args:
            rejected: ``(path, reason)`` pairs from the last import.
        """
        if not hasattr(self, "files_rejected_label"):
            return
        if not rejected:
            self.files_rejected_label.configure(text="")
            return
        shown = [f"{path} ({reason})" for path, reason in rejected[:5]]
        if len(rejected) > 5:
            shown.append(f"+{len(rejected) - 5}")
        self.files_rejected_label.configure(
            text=self.localization_manager.get_string("files_rejected", items="; ".join(shown))
        )

    def _set_file_status_threadsafe(self, path: str, status: str) -> None:
        """Record a status change from any thread and schedule the UI update.

        Args:
            path: Queued file path.
            status: One of pending / transcribing / done / error.
        """
        self._files_status[path] = status
        self.after(0, self._set_file_status, path, status)

    def _set_file_status(self, path: str, status: str) -> None:
        """Update one queue row status label (main thread only).

        Args:
            path: Queued file path.
            status: One of pending / transcribing / done / error.
        """
        label = self._files_status_labels.get(path)
        if label is None:
            return
        try:
            if not label.winfo_exists():
                self._files_status_labels.pop(path, None)
                return
            label.configure(
                text=self.localization_manager.get_string(self._STATUS_KEYS[status]),
                text_color=self._STATUS_COLORS[status],
            )
        except Exception as exc:
            logger.debug("Status label update skipped: %s", exc)

    # ── Queue actions ────────────────────────────────────────────────
    def transcribe_all_queue(self) -> None:
        """Start the single sequential worker thread for the pending queue.

        Does nothing when a worker is already running or the queue is empty.
        """
        self._ensure_files_queue_state()
        with self._files_worker_lock:
            if self._files_worker_running or not self._files_queue:
                return
            self._files_worker_running = True
        self.after(
            0,
            self.update_status,
            self.localization_manager.get_string("files_status_transcribing"),
            "yellow",
        )
        threading.Thread(
            target=self._files_queue_worker, daemon=True, name="files-queue-worker"
        ).start()

    def clear_files_queue(self) -> None:
        """Clear the pending queue, status map and queue rows."""
        self._ensure_files_queue_state()
        with self._files_worker_lock:
            self._files_queue.clear()
            self._files_status.clear()
            self._files_status_labels.clear()
        for widget in self.files_queue_frame.winfo_children():
            widget.destroy()
        self._show_rejected([])

    # ── Sequential worker (exactly one thread at a time) ────
    def _files_queue_worker(self) -> None:
        """Iterate the queue sequentially until no pending file remains."""
        pending_count = len(self._files_queue)
        logger.info("Files queue worker started (%d pending)", pending_count)
        done_count = 0
        while True:
            path = self._next_pending_file()
            if path is None:
                break
            if self._process_one_file(path):
                done_count += 1
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
                if self._files_status.get(path) == "pending":
                    return path
        return None

    def _process_one_file(self, path: str) -> bool:
        """Transcribe one file through the existing retranscription flow.

        Mirrors ``App._retranscribe_thread``: transcribe_with_groq →
        display_transcription → save_transcription_entry (same entry keys).
        UI updates are scheduled on the main thread; a failure marks only
        this file as error and never stops the queue.

        Args:
            path: Audio file path to transcribe.

        Returns:
            True when the file was transcribed and saved successfully.
        """
        self._set_file_status_threadsafe(path, "transcribing")
        try:
            text = self.transcriber.transcribe_with_groq(path)
        except Exception as exc:
            logger.error("Queued file transcription failed: %s", exc)
            self._set_file_status_threadsafe(path, "error")
            return False
        if not text:
            self._set_file_status_threadsafe(path, "error")
            return False
        try:
            self.after(0, self.display_transcription, text)
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
            logger.error("Queued file result could not be saved: %s", exc)
            self._set_file_status_threadsafe(path, "error")
            return False
        self._set_file_status_threadsafe(path, "done")
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
