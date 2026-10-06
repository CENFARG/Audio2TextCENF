"""
SupervisorViewMixin — F2 Supervisor tab (AI-response drafting workbench).

Thin CustomTkinter mixin (HC-02 pattern): numbered entries (AI quote +
correction), insertable context blocks, per-entry record toggle, 500 ms
debounced autosave, CRUD with confirm, assembled copy to the clipboard.
Pure glue lives at module level (unit-tested headlessly); Tk widgets by
inspection + import smoke. Host dependencies come from the App instance.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.context_blocks import assemble_all

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


def format_entry_label(number: int, status_label: str) -> str:
    """Format the row header label: ``#N · status``."""
    return f"#{number} · {status_label}"


def build_copy_payload(entries) -> str:
    """Assemble entries via the store assembler (numeric order, blank-line separated)."""
    return assemble_all(entries)


class SupervisorViewMixin:
    """Mixin providing the Supervisor tab (created after the main tab)."""

    # Host attributes (HC-02 mixin pattern; provided by ui.app.App at runtime).
    localization_manager: Any
    config_manager: Any
    transcriber: Any
    main_frame: Any
    after: Any
    after_cancel: Any

    def create_supervisor_tab(self) -> None:
        """Build the Supervisor tab: state, widgets and initial render."""
        import customtkinter as ctk

        try:
            from ui.app import DesignSystem  # type: ignore[assignment]
        except ImportError:  # pragma: no cover - direct-run convenience

            class DesignSystem:  # type: ignore[no-redef]
                """Fallback palette matching ui.app.DesignSystem."""

                COLORS = {"primary": "#2563EB", "warning": "#F59E0B"}
                TYPOGRAPHY = {
                    "heading_medium": ("Segoe UI", 16, "bold"),
                    "body_small": ("Segoe UI", 12, "normal"),
                }

        import backend.context_blocks as context_blocks
        from backend.supervisor_recorder import SupervisorRecorder
        from backend.supervisor_store import SupervisorStore

        loc = self.localization_manager
        self.supervisor_store = SupervisorStore(
            self.config_manager.get("supervisor_data_path", "supervisor_entries.json")
        )
        self.context_blocks = context_blocks.load_context_blocks(
            self.config_manager.get("context_blocks_dir", context_blocks.DEFAULT_CONTEXT_BLOCKS_DIR)
        )
        self.supervisor_recorder = SupervisorRecorder(
            on_text=lambda text: self.after(0, self._supervisor_on_record_text, text),
            transcribe_fn=self.transcriber.transcribe_with_groq,
            main_transcriber=self.transcriber,
        )
        self._supervisor_debounce = DebounceTimer()
        self._supervisor_rows: dict[int, dict[str, Any]] = {}
        self._supervisor_selected: int | None = None
        self._supervisor_recording_number: int | None = None

        tab = self.main_frame.tab(loc.get_string("tab_supervisor"))
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            tab,
            text=loc.get_string("supervisor_title"),
            anchor="w",
            font=DesignSystem.TYPOGRAPHY["heading_medium"],
        ).grid(row=0, column=0, padx=10, pady=(5, 0), sticky="ew")
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.grid(row=0, column=0, padx=10, pady=(36, 5), sticky="ew")
        ctk.CTkButton(
            bar,
            text=loc.get_string("supervisor_new_entry"),
            width=130,
            command=self._supervisor_new_entry,
        ).pack(side="left", padx=(0, 5))
        names = [b.name for b in self.context_blocks] or [loc.get_string("supervisor_no_blocks")]
        self._supervisor_block_menu = ctk.CTkOptionMenu(bar, values=names, width=170)
        self._supervisor_block_menu.pack(side="left", padx=5)
        ctk.CTkButton(
            bar,
            text=loc.get_string("supervisor_insert_block"),
            width=120,
            state="normal" if self.context_blocks else "disabled",
            command=self._supervisor_insert_block,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            bar,
            text=loc.get_string("supervisor_copy_all"),
            width=110,
            fg_color=DesignSystem.COLORS["primary"],
            command=self._supervisor_copy_all,
        ).pack(side="right")
        self.supervisor_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.supervisor_scroll.grid(row=1, column=0, padx=6, pady=5, sticky="nsew")
        self.supervisor_status_label = ctk.CTkLabel(
            tab,
            text="",
            anchor="w",
            wraplength=520,
            font=DesignSystem.TYPOGRAPHY["body_small"],
            text_color=DesignSystem.COLORS["warning"],
        )
        self.supervisor_status_label.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="ew")
        self._supervisor_rebuild_rows()

    def _supervisor_rebuild_rows(self) -> None:
        """Re-render every entry row after a structural change (CRUD)."""
        for widget in self.supervisor_scroll.winfo_children():
            widget.destroy()
        self._supervisor_rows = {}
        entries = self.supervisor_store.all()
        for entry in entries:
            self._supervisor_build_row(entry)
        self._supervisor_selected = resolve_selection(
            [e.number for e in entries], self._supervisor_selected
        )

    def _supervisor_build_row(self, entry) -> None:
        """Build one entry row: header + quote + response textboxes."""
        import customtkinter as ctk

        loc = self.localization_manager
        number = entry.number
        is_sent = entry.status == "sent"
        row = ctk.CTkFrame(self.supervisor_scroll, fg_color="transparent")
        row.pack(fill="x", pady=(8, 2), padx=4)
        status_key = "supervisor_status_sent" if is_sent else "supervisor_status_draft"
        ctk.CTkLabel(
            row, text=format_entry_label(number, loc.get_string(status_key)), anchor="w"
        ).pack(side="left")
        record_btn = ctk.CTkButton(
            row,
            text=loc.get_string("supervisor_record"),
            width=90,
            command=lambda n=number: self._supervisor_toggle_record(n),
        )
        record_btn.pack(side="right", padx=(4, 0))
        for kwargs in (
            {
                "text": loc.get_string("supervisor_copy_entry", number=number),
                "width": 110,
                "command": lambda n=number: self._supervisor_copy_entry(n),
            },
            {
                "text": loc.get_string("supervisor_reopen" if is_sent else "supervisor_mark_sent"),
                "width": 90,
                "fg_color": "transparent",
                "border_width": 1,
                "command": lambda n=number: self._supervisor_toggle_status(n),
            },
            {
                "text": "🗑",
                "width": 36,
                "fg_color": "transparent",
                "border_width": 1,
                "command": lambda n=number: self._supervisor_delete_entry(n),
            },
        ):
            ctk.CTkButton(row, **kwargs).pack(side="right", padx=4)

        # CTkTextbox no soporta placeholder_text (crashea en Tcl/Tk estricto):
        # el campo arranca vacío y el contenido real se inserta abajo.
        quote = ctk.CTkTextbox(row, height=50)
        quote.pack(fill="x", pady=(2, 0))
        if entry.quote:
            quote.insert("1.0", entry.quote)
        response = ctk.CTkTextbox(row, height=110)
        response.pack(fill="x", pady=(2, 4))
        if entry.response:
            response.insert("1.0", entry.response)
        for textbox in (quote, response):
            textbox.bind("<KeyRelease>", lambda _e, n=number: self._supervisor_schedule_autosave(n))
            textbox.bind("<FocusOut>", lambda _e, n=number: self._supervisor_flush_entry(n))
        rows_entry = {"quote": quote, "response": response, "record": record_btn}
        self._supervisor_rows[number] = rows_entry

    def _supervisor_schedule_autosave(self, number: int) -> None:
        """Debounce-schedule a store flush for one entry (keystroke path)."""
        self._supervisor_debounce.schedule(
            self.after, self.after_cancel, lambda n=number: self._supervisor_flush_entry(n)
        )

    def _supervisor_flush_entry(self, number: int) -> None:
        """Persist the current textbox contents of one entry (autosave)."""
        row = self._supervisor_rows.get(number)
        if row is None:
            return
        self.supervisor_store.update_entry(
            number,
            quote=row["quote"].get("1.0", "end-1c"),
            response=row["response"].get("1.0", "end-1c"),
        )

    def _supervisor_new_entry(self) -> None:
        """Create the next numbered entry and focus its response field."""
        entry = self.supervisor_store.create_entry()
        self._supervisor_selected = entry.number
        self._supervisor_rebuild_rows()
        row = self._supervisor_rows.get(entry.number)
        if row is not None:
            row["response"].focus_set()
        self._supervisor_set_status(f"#{entry.number}")

    def _supervisor_delete_entry(self, number: int) -> None:
        """Delete an entry after confirmation; numbers are never reassigned."""
        from tkinter import messagebox

        loc = self.localization_manager
        if not messagebox.askyesno(
            loc.get_string("tab_supervisor"),
            loc.get_string("supervisor_delete_confirm", number=number),
        ):
            return
        self.supervisor_store.delete_entry(number)
        self._supervisor_rebuild_rows()
        self._supervisor_set_status(loc.get_string("supervisor_deleted", number=number))

    def _supervisor_toggle_status(self, number: int) -> None:
        """Toggle draft <-> sent (state machine guards illegal transitions)."""
        from backend.supervisor_store import STATUS_DRAFT, STATUS_SENT

        entry = self.supervisor_store.get(number)
        if entry is None:
            return
        target = STATUS_DRAFT if entry.status == STATUS_SENT else STATUS_SENT
        self.supervisor_store.set_status(number, target)
        self._supervisor_rebuild_rows()

    def _supervisor_copy_entry(self, number: int) -> None:
        """Copy one entry assembled (``N. "quote"\\n: response``) to the clipboard."""
        entry = self.supervisor_store.get(number)
        if entry is None:
            return
        self._supervisor_copy_to_clipboard(build_copy_payload([entry]))

    def _supervisor_copy_all(self) -> None:
        """Copy every entry assembled in numeric order to the clipboard."""
        self._supervisor_copy_to_clipboard(build_copy_payload(self.supervisor_store.all()))

    def _supervisor_copy_to_clipboard(self, text: str) -> None:
        """Best-effort clipboard write with a localized confirmation."""
        loc = self.localization_manager
        try:
            import pyperclip

            pyperclip.copy(text)
            self._supervisor_set_status(loc.get_string("supervisor_copied"))
        except Exception as exc:
            logger.error("Supervisor clipboard copy failed: %s", exc)
            self._supervisor_set_status(f"{loc.get_string('supervisor_copied')} (error)")

    def _supervisor_insert_block(self) -> None:
        """Insert the selected block body at the response cursor (records id)."""
        loc = self.localization_manager
        number = self._supervisor_selected
        if number is None:
            self._supervisor_set_status(loc.get_string("supervisor_no_blocks"))
            return
        row = self._supervisor_rows.get(number)
        name = self._supervisor_block_menu.get()
        block = next((b for b in self.context_blocks if b.name == name), None)
        if row is None or block is None:
            self._supervisor_set_status(loc.get_string("supervisor_no_blocks"))
            return
        response = row["response"]
        content = response.get("1.0", "end-1c")
        line, col = parse_tk_index(response.index("insert"))
        cursor = tk_index_to_char_index(content, line, col)
        new_text = compute_inserted_text(content, block.body, cursor)
        response.delete("1.0", "end")
        response.insert("1.0", new_text)
        entry = self.supervisor_store.get(number)
        self.supervisor_store.update_entry(
            number,
            response=new_text,
            blocks=append_block_id(entry.blocks, block.id) if entry else [],
        )

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

    def _supervisor_set_status(self, message: str) -> None:
        """Show a transient status message on the bottom label."""
        self.supervisor_status_label.configure(text=message)
