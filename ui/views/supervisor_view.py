"""
SupervisorViewMixin — F2 Supervisor tab: workbench UI + A4 Prompter Gate glue.
HC-02 pattern; pure helpers in ui.views.supervisor_helpers; Tk by inspection.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.prompter_gate import PrompterGate, build_prompter_messages, select_block_bodies
from backend.supervisor_store import DEFAULT_SESSION
from ui.views.supervisor_helpers import (
    DebounceTimer,
    SupervisorBlocksDialogMixin,
    SupervisorRecordMixin,
    build_copy_payload,
    format_entry_label,
    load_design_system,
    resolve_selection,
    select_visible_entries,
)

logger = logging.getLogger(__name__)


class SupervisorViewMixin(SupervisorBlocksDialogMixin, SupervisorRecordMixin):
    """Mixin providing the Supervisor tab (created after the main tab)."""

    # Host attributes (HC-02 mixin pattern; provided by ui.app.App at runtime).
    localization_manager: Any
    config_manager: Any
    transcriber: Any
    main_frame: Any
    after: Any
    after_cancel: Any
    _prompter_llm: Any

    def create_supervisor_tab(self) -> None:
        """Build the Supervisor tab: state, widgets and initial render."""
        import customtkinter as ctk

        DesignSystem = load_design_system()

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
        self.prompter_gate = PrompterGate(self.config_manager.get, self._prompter_llm)
        self._supervisor_debounce = DebounceTimer()
        self._supervisor_rows: dict[int, dict[str, Any]] = {}
        self._supervisor_selected: int | None = None
        self._supervisor_recording_number: int | None = None

        tab = self.main_frame.tab(loc.get_string("tab_supervisor"))
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(
            tab,
            text=loc.get_string("supervisor_title"),
            anchor="w",
            font=DesignSystem.TYPOGRAPHY["heading_medium"],
        ).grid(row=0, column=0, padx=10, pady=(5, 0), sticky="ew")
        # REQ-2: session selector (persisted in supervisor_last_session) + filter.
        self._supervisor_session_only = False
        self._supervisor_session_var = ctk.StringVar(
            value=self.config_manager.get("supervisor_last_session", DEFAULT_SESSION)
            or DEFAULT_SESSION
        )
        session_bar = ctk.CTkFrame(tab, fg_color="transparent")
        session_bar.grid(row=1, column=0, padx=10, pady=(4, 0), sticky="ew")
        ctk.CTkLabel(session_bar, text=loc.get_string("supervisor_session_label"), anchor="w").pack(
            side="left", padx=(0, 6)
        )
        self._supervisor_session_combo = ctk.CTkComboBox(
            session_bar,
            values=self._supervisor_known_sessions(),
            variable=self._supervisor_session_var,
            width=150,
            command=self._supervisor_on_session_changed,
        )
        self._supervisor_session_combo.pack(side="left")
        self._supervisor_session_switch = ctk.CTkSwitch(
            session_bar,
            text=loc.get_string("supervisor_session_filter"),
            command=self._supervisor_on_session_filter_toggled,
        )
        self._supervisor_session_switch.pack(side="right")
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.grid(row=2, column=0, padx=10, pady=(6, 5), sticky="ew")
        # UX-3: compact widths keep "Copiar todo" visible on the 590px window.
        ctk.CTkButton(
            bar,
            text=loc.get_string("supervisor_new_entry"),
            width=118,
            command=self._supervisor_new_entry,
        ).pack(side="left", padx=(0, 3))
        # REQ-3: one "Bloques" button opens the multi-select dialog; insertion
        # happens inside that dialog ("Insertar seleccionados").
        ctk.CTkButton(
            bar,
            text=loc.get_string("supervisor_blocks_button"),
            width=92,
            state="normal" if self.context_blocks else "disabled",
            command=self._supervisor_open_blocks_dialog,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            bar,
            text=loc.get_string("supervisor_copy_all"),
            width=98,
            fg_color=DesignSystem.COLORS["primary"],
            command=self._supervisor_copy_all,
        ).pack(side="right", padx=(3, 0))
        self._supervisor_prompter_switch: ctk.CTkSwitch = ctk.CTkSwitch(
            bar,
            text=loc.get_string("supervisor_prompter_button"),
            command=lambda: self.config_manager.set(
                "prompter_gate_auto", bool(self._supervisor_prompter_switch.get())
            ),
        )
        if self.config_manager.get("prompter_gate_auto", True):
            self._supervisor_prompter_switch.select()
        self._supervisor_prompter_switch.pack(side="right", padx=(6, 3))
        self.supervisor_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.supervisor_scroll.grid(row=3, column=0, padx=6, pady=5, sticky="nsew")
        self.supervisor_status_label = ctk.CTkLabel(
            tab,
            text="",
            anchor="w",
            wraplength=520,
            font=DesignSystem.TYPOGRAPHY["body_small"],
            text_color=DesignSystem.COLORS["warning"],
        )
        self.supervisor_status_label.grid(row=4, column=0, padx=10, pady=(0, 8), sticky="ew")
        self._supervisor_rebuild_rows()

    def _supervisor_current_session(self) -> str:
        """REQ-2: session name currently selected in the workbench selector."""
        var = getattr(self, "_supervisor_session_var", None)
        value = var.get() if var is not None else ""
        return str(value or "").strip() or DEFAULT_SESSION

    def _supervisor_known_sessions(self) -> list[str]:
        """REQ-2: combo values — default first, then every store session sorted."""
        sessions = {entry.session for entry in self.supervisor_store.all()}
        sessions.add(self._supervisor_current_session())
        return [DEFAULT_SESSION, *sorted(sessions - {DEFAULT_SESSION})]

    def _supervisor_on_session_changed(self, _value: str = "") -> None:
        """REQ-2: persist the selected session and re-render the entry list."""
        self.config_manager.set("supervisor_last_session", self._supervisor_current_session())
        self._supervisor_rebuild_rows()

    def _supervisor_on_session_filter_toggled(self) -> None:
        """REQ-2: apply/clear the "solo esta sesión" filter and re-render."""
        self._supervisor_session_only = bool(self._supervisor_session_switch.get())
        self._supervisor_rebuild_rows()

    def _supervisor_rebuild_rows(self) -> None:
        """Re-render the visible entry rows (REQ-2: session filter honored)."""
        for widget in self.supervisor_scroll.winfo_children():
            widget.destroy()
        self._supervisor_rows = {}
        entries = select_visible_entries(
            self.supervisor_store.all(),
            self._supervisor_current_session(),
            self._supervisor_session_only,
        )
        for entry in entries:
            self._supervisor_build_row(entry)
        self._supervisor_selected = resolve_selection(
            [e.number for e in entries], self._supervisor_selected
        )

    def _supervisor_build_row(self, entry) -> None:
        """Build one entry row: header (label + actions) + full-width textareas (UX-2b grid)."""
        import customtkinter as ctk

        loc = self.localization_manager
        number = entry.number
        is_sent = entry.status == "sent"
        row = ctk.CTkFrame(self.supervisor_scroll, fg_color="transparent")
        row.pack(fill="x", pady=(8, 2), padx=4)
        row.grid_columnconfigure(0, weight=1)

        # Header line: entry label left, all actions right.
        header = ctk.CTkFrame(row, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        status_key = "supervisor_status_sent" if is_sent else "supervisor_status_draft"
        ctk.CTkLabel(
            header,
            text=format_entry_label(number, loc.get_string(status_key), entry.session),
            anchor="w",
        ).pack(side="left")
        record_btn = ctk.CTkButton(
            header,
            text=loc.get_string("supervisor_record"),
            width=88,
            command=lambda n=number: self._supervisor_toggle_record(n),
        )
        record_btn.pack(side="right", padx=(4, 0))
        for kwargs in (
            {
                "text": loc.get_string("supervisor_prompter_button"),
                "width": 88,
                "command": lambda n=number: self._supervisor_start_prompter(n),
            },
            {
                "text": loc.get_string("supervisor_copy_entry", number=number),
                "width": 106,
                "command": lambda n=number: self._supervisor_copy_entry(n),
            },
            {
                "text": loc.get_string("supervisor_reopen" if is_sent else "supervisor_mark_sent"),
                "width": 88,
                "command": lambda n=number: self._supervisor_toggle_status(n),
            },
            {
                "text": "🗑",
                "width": 34,
                "command": lambda n=number: self._supervisor_delete_entry(n),
            },
        ):
            ctk.CTkButton(header, **kwargs).pack(side="right", padx=3)

        # CTkTextbox no soporta placeholder_text (crashea en Tcl/Tk estricto).
        quote = ctk.CTkTextbox(row, height=50)
        quote.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        if entry.quote:
            quote.insert("1.0", entry.quote)
        response = ctk.CTkTextbox(row, height=110)
        response.grid(row=2, column=0, sticky="ew", pady=(2, 4))
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
        """Persist the current textboxes of one entry, then run the A4 auto gate."""
        row = self._supervisor_rows.get(number)
        if row is None:
            return
        response = row["response"].get("1.0", "end-1c")
        self.supervisor_store.update_entry(
            number, quote=row["quote"].get("1.0", "end-1c"), response=response
        )
        if self.prompter_gate.auto_enabled() and self.prompter_gate.evaluate(response).trigger:
            self._supervisor_start_prompter(number)

    def _supervisor_new_entry(self) -> None:
        """Create the next numbered entry in the current session and focus it."""
        session = self._supervisor_current_session()
        entry = self.supervisor_store.create_entry(session=session)
        self.config_manager.set("supervisor_last_session", session)
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
        payload = build_copy_payload([entry])
        if not payload.strip():
            # C-3: no quote AND no response copies nothing — say it instead.
            self._supervisor_set_status(
                self.localization_manager.get_string("supervisor_copy_empty", number=number)
            )
            return
        self._supervisor_copy_to_clipboard(payload)

    def _supervisor_copy_all(self) -> None:
        """Copy visible entries assembled in numeric order (REQ-2: session filter)."""
        entries = select_visible_entries(
            self.supervisor_store.all(),
            self._supervisor_current_session(),
            self._supervisor_session_only,
        )
        payload = build_copy_payload(entries)
        if not payload.strip():
            # C-3: nothing to copy anywhere — same localized feedback.
            self._supervisor_set_status(
                self.localization_manager.get_string("supervisor_copy_empty", number="").rstrip()
            )
            return
        self._supervisor_copy_to_clipboard(payload)

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

    def _supervisor_set_status(self, message: str) -> None:
        """Show a transient status message on the bottom label."""
        self.supervisor_status_label.configure(text=message)

    def _supervisor_start_prompter(self, number: int) -> bool:
        """A4: run one Prompter pass for an entry (manual button or auto gate)."""
        entry = self.supervisor_store.get(number)
        if entry is None or not str(entry.response or "").strip():
            return False
        if self.prompter_gate.is_running(number):
            self._supervisor_set_status(
                self.localization_manager.get_string("supervisor_prompter_running")
            )
            return False
        quote = str(entry.quote or "").strip()
        blocks = select_block_bodies(self.context_blocks, entry.blocks)
        messages = build_prompter_messages(entry.response, blocks, quote or None)
        started = self.prompter_gate.start(
            number,
            messages,
            on_done=lambda n, t: self.after(0, self._supervisor_on_prompter_result, n, t, None),
            on_error=lambda n, e: self.after(0, self._supervisor_on_prompter_result, n, None, e),
        )
        if started:
            self._supervisor_set_status(
                self.localization_manager.get_string("supervisor_prompter_running")
            )
        return started

    def _supervisor_on_prompter_result(
        self, number: int, text: str | None, error: str | None
    ) -> None:
        """A4: pass outcome — replace the response on success, keep the draft on error."""
        if error is not None:
            logger.error("Supervisor Prompter pass failed on #%s: %s", number, error)
            self._supervisor_set_status(
                self.localization_manager.get_string("supervisor_prompter_error")
            )
            return
        self.supervisor_store.update_entry(number, response=text or "")
        row = self._supervisor_rows.get(number)
        if row is not None:
            row["response"].delete("1.0", "end")
            row["response"].insert("1.0", text or "")
        self._supervisor_set_status(
            self.localization_manager.get_string("supervisor_prompter_done")
        )
