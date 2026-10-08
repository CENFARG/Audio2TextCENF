"""
Supervisor helpers — pure glue + dialog/record mixins for the Supervisor tab.

Extracted from ``ui/views/supervisor_view.py`` (behavior-preserving split,
files ≤400 lines rule): headless-unit-tested pure functions, the autosave
debounce, the REQ-3 multi-select blocks dialog logic and the per-entry
record lifecycle. Tk widget construction and session/copy glue stay in
:mod:`ui.views.supervisor_view`.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.context_blocks import assemble_all
from backend.supervisor_store import DEFAULT_SESSION

logger = logging.getLogger(__name__)

#: Autosave debounce window (spec: >= 500 ms keystroke updates).
AUTOSAVE_DEBOUNCE_MS = 500


class DebounceTimer:
    """Trailing-edge autosave debounce: rescheduling cancels the prior flush."""

    def __init__(self, delay_ms: int = AUTOSAVE_DEBOUNCE_MS) -> None:
        self.delay_ms = delay_ms
        self._pending: object | None = None

    @property
    def pending(self) -> bool:
        """Whether a flush callback is currently scheduled."""
        return self._pending is not None

    def schedule(self, after, after_cancel, flush) -> object:
        """Schedule ``flush`` after the delay, cancelling any pending call first."""
        self.cancel(after_cancel)
        self._pending = after(self.delay_ms, flush)
        return self._pending

    def cancel(self, after_cancel) -> bool:
        """Cancel the pending flush; ``True`` when a call was cancelled."""
        if self._pending is None:
            return False
        try:
            after_cancel(self._pending)
        except Exception:  # pragma: no cover - Tk token already fired
            logger.debug("Supervisor autosave cancel failed", exc_info=True)
        self._pending = None
        return True


def parse_tk_index(index_str: str) -> tuple[int, int]:
    """Parse ``"line.col"`` into ``(line, col)`` ints; ``(1, 0)`` when unparsable."""
    try:
        line_s, col_s = str(index_str).split(".", 1)
        return int(line_s), int(col_s)
    except ValueError:
        return 1, 0


def tk_index_to_char_index(content: str, line: int, col: int) -> int:
    """Convert a Tk ``line.col`` position to a char offset (both axes clamped)."""
    lines = content.split("\n")
    line = max(1, int(line))
    if line > len(lines):
        return len(content)
    prefix = sum(len(text) + 1 for text in lines[: line - 1])
    return prefix + min(max(0, int(col)), len(lines[line - 1]))


def compute_inserted_text(content: str, insert_text: str, char_index: int | None) -> str:
    """Compose ``content`` with ``insert_text`` at ``char_index`` (None/past-end appends)."""
    if char_index is None or char_index >= len(content):
        return content + insert_text
    if char_index <= 0:
        return insert_text + content
    return content[:char_index] + insert_text + content[char_index:]


def resolve_selection(numbers: list[int], current: int | None) -> int | None:
    """Keep ``current`` if still present, else the first number, else ``None``."""
    if current in numbers:
        return current
    return numbers[0] if numbers else None


def append_block_id(ids: list[str], block_id: str) -> list[str]:
    """Append ``block_id`` without duplicates; empty ids ignored; new list returned."""
    if not block_id or block_id in ids:
        return list(ids)
    return [*ids, block_id]


def select_blocks(check_state: dict[str, bool], blocks) -> list:
    """REQ-3: map checkbox state ``{block_id: bool}`` to the selected blocks.

    Blocks are returned in loaded (list) order — sorted by name — never in
    check order; unknown ids in the state are ignored; missing or False ids
    are excluded.
    """
    return [block for block in blocks if check_state.get(block.id)]


def compute_multi_insert(content: str, texts: list[str], char_index: int | None) -> str:
    """REQ-3: insert each text at the cursor sequentially, in list order.

    The cursor advances by every inserted body so later texts land after
    earlier ones; ``None`` (or a past-end index) appends.
    """
    cursor = char_index
    for text in texts:
        content = compute_inserted_text(content, text, cursor)
        if cursor is not None:
            cursor += len(text)
    return content


def format_entry_label(number: int, status_label: str, session: str = "") -> str:
    """Format the row header label: ``#N · status`` (REQ-2: ``· session`` suffix).

    Args:
        number: Historical entry number.
        status_label: Localized status word (``borrador`` / ``enviada``).
        session: Entry session name; appended when non-empty so entries from
            every session stay distinguishable in the unfiltered list.

    Returns:
        The row header text.
    """
    label = f"#{number} · {status_label}"
    return f"{label} · {session}" if session else label


def select_visible_entries(entries, current_session: str, only_session: bool) -> list:
    """REQ-2: entries shown and copied under the "solo esta sesión" switch.

    Args:
        entries: All store entries in numeric order.
        current_session: Session selected in the workbench selector.
        only_session: Switch state — ``True`` keeps only entries whose
            session matches ``current_session``; ``False`` returns them all.

    Returns:
        The filtered entries, original order preserved.
    """
    if not only_session:
        return list(entries)
    return [entry for entry in entries if entry.session == current_session]


def build_copy_payload(entries) -> str:
    """Assemble entries via the store assembler (numeric order, blank-line separated)."""
    return assemble_all(entries)


def load_design_system():
    """Resolve ``ui.app.DesignSystem`` with a headless fallback palette."""
    try:
        from ui.app import DesignSystem  # type: ignore[assignment]
    except ImportError:  # pragma: no cover - direct-run convenience

        class DesignSystem:  # type: ignore[no-redef]
            """Fallback palette matching ui.app.DesignSystem."""

            COLORS = {
                "primary": "#2563EB",
                "warning": "#F59E0B",
                "text_primary": "#E2E8F0",
            }
            TYPOGRAPHY = {
                "heading_medium": ("Segoe UI", 16, "bold"),
                "body_small": ("Segoe UI", 12, "normal"),
            }

    return DesignSystem


class SupervisorBlocksDialogMixin:
    """Mixin with the REQ-3 multi-select context-blocks dialog logic."""

    # Host attributes (HC-02 mixin pattern; provided by ui.app.App at runtime).
    localization_manager: Any
    context_blocks: Any
    supervisor_store: Any
    _supervisor_selected: Any
    _supervisor_rows: Any
    _supervisor_set_status: Any

    def _supervisor_open_blocks_dialog(self) -> None:
        """REQ-3: open the multi-select context-blocks dialog.

        Lists ALL loaded blocks (sorted by name) with one checkbox each and
        the description under the name; "Insertar seleccionados" inserts the
        checked bodies at the response cursor and closes the window.
        """
        import customtkinter as ctk

        DesignSystem = load_design_system()

        loc = self.localization_manager
        dialog = ctk.CTkToplevel(self)
        dialog.title(loc.get_string("supervisor_blocks_title"))
        dialog.geometry("360x430")
        dialog.transient(self)  # type: ignore[arg-type]  # HC-02: host is a Tk window
        dialog.attributes("-topmost", True)
        frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        check_vars: dict[str, Any] = {}
        for block in self.context_blocks:  # loaded order: sorted by name
            var = ctk.BooleanVar(value=False)
            check_vars[block.id] = var
            ctk.CTkCheckBox(frame, text=block.name, variable=var).pack(anchor="w", pady=(6, 0))
            if block.description:
                ctk.CTkLabel(
                    frame,
                    text=block.description,
                    anchor="w",
                    wraplength=310,
                    justify="left",
                    font=DesignSystem.TYPOGRAPHY["body_small"],
                    text_color=DesignSystem.COLORS["text_primary"],
                ).pack(anchor="w", padx=(28, 0))
        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=10, pady=(4, 10))
        ctk.CTkButton(
            buttons,
            text=loc.get_string("supervisor_insert_selected"),
            command=lambda: self._supervisor_insert_selected_blocks(
                {block_id: bool(var.get()) for block_id, var in check_vars.items()},
                on_done=dialog.destroy,
            ),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            buttons,
            text=loc.get_string("supervisor_close"),
            fg_color="transparent",
            border_width=1,
            command=dialog.destroy,
        ).pack(side="right")

    def _supervisor_insert_selected_blocks(self, check_state, on_done=None) -> None:
        """REQ-3: insert every checked block at the response cursor, in order.

        Bodies go in as one cursor-anchored sequence in list order and each
        block id is recorded in the entry's ``blocks`` list (dedup). With no
        selected entry the localized select-entry-first hint is shown.
        ``on_done`` runs after a successful insert (dialog closes itself).
        """
        loc = self.localization_manager
        number = self._supervisor_selected
        if number is None:
            # C-6: the real problem is the missing entry, not the blocks.
            self._supervisor_set_status(loc.get_string("supervisor_select_entry_first"))
            return
        selected = select_blocks(check_state, self.context_blocks)
        row = self._supervisor_rows.get(number)
        if row is None or not selected:
            self._supervisor_set_status(loc.get_string("supervisor_no_blocks"))
            return
        response = row["response"]
        content = response.get("1.0", "end-1c")
        line, col = parse_tk_index(response.index("insert"))
        cursor = tk_index_to_char_index(content, line, col)
        new_text = compute_multi_insert(content, [block.body for block in selected], cursor)
        response.delete("1.0", "end")
        response.insert("1.0", new_text)
        entry = self.supervisor_store.get(number)
        blocks = list(entry.blocks) if entry else []
        for block in selected:
            blocks = append_block_id(blocks, block.id)
        self.supervisor_store.update_entry(number, response=new_text, blocks=blocks)
        if on_done is not None:
            on_done()


class SupervisorRecordMixin:
    """Mixin with the per-entry record button lifecycle (capture glue)."""

    # Host attributes (HC-02 mixin pattern; provided by ui.app.App at runtime).
    localization_manager: Any
    supervisor_recorder: Any
    supervisor_store: Any
    _supervisor_recording_number: Any
    _supervisor_rows: Any
    _supervisor_set_status: Any

    def _supervisor_toggle_record(self, number: int) -> None:
        """Toggle the per-entry record button (one supervisor recording at a time)."""
        loc = self.localization_manager
        recorder = self.supervisor_recorder
        if recorder.recording:
            self._supervisor_set_status(loc.get_string("supervisor_transcribing"))
            recorder.stop()
            self._supervisor_reset_record_button()
            return
        if not recorder.start():
            reason = recorder.refusal_reason
            key = (
                "supervisor_recording_blocked" if reason == "main_recording" else "supervisor_busy"
            )
            logger.warning("Supervisor recording refused (%s)", reason)
            self._supervisor_set_status(loc.get_string(key))
            return
        self._supervisor_recording_number = number
        row = self._supervisor_rows.get(number)
        if row is not None:
            row["record"].configure(text=loc.get_string("supervisor_record_stop"))

    def _supervisor_reset_record_button(self) -> None:
        """Restore the record button label after a capture finishes."""
        number = self._supervisor_recording_number
        self._supervisor_recording_number = None
        row = self._supervisor_rows.get(number) if number is not None else None
        if row is not None:
            row["record"].configure(text=self.localization_manager.get_string("supervisor_record"))

    def _supervisor_on_record_text(self, text) -> None:
        """Deliver a finished fragment transcript into the recorded entry."""
        loc = self.localization_manager
        number = self._supervisor_recording_number
        self._supervisor_reset_record_button()
        if number is None:
            return
        if text is None:
            # C-1: capture failed upstream — clear "Transcribiendo..." with a
            # specific localized error instead of the generic failed message.
            self._supervisor_set_status(loc.get_string("supervisor_recording_error"))
            return
        if not text:
            self._supervisor_set_status(loc.get_string("supervisor_transcription_failed"))
            return
        entry = self.supervisor_store.get(number)
        merged = f"{entry.response} {text}".strip() if entry else text
        self.supervisor_store.update_entry(number, response=merged)
        row = self._supervisor_rows.get(number)
        if row is not None:
            row["response"].delete("1.0", "end")
            row["response"].insert("1.0", merged)
        self._supervisor_set_status(loc.get_string("supervisor_transcribed"))
