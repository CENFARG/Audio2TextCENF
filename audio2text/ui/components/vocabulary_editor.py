"""@File: audio2text/ui/components/vocabulary_editor.py
@Description: Custom vocabulary editor — add/remove/edit correction terms with enabled toggle.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.theme.theme import Colors, Spacing, Typography


class VocabularyEditor(ft.Column):
    """Editable list of custom vocabulary corrections.

    Features:
    - List of corrections with enabled toggle.
    - Add new correction (original → correction).
    - Remove correction.
    - Save button to persist changes.
    """

    def __init__(
        self,
        t: LocalizationManager,
        entries: list[dict[str, object]] | None = None,
        on_add: Callable[[str, str], None] | None = None,
        on_remove: Callable[[str], None] | None = None,
        on_toggle: Callable[[str, bool], None] | None = None,
        on_save: Callable[[list[dict[str, object]]], None] | None = None,
    ) -> None:
        """Initialize the vocabulary editor.

        Args:
            t: Localization manager for translated strings.
            entries: Initial vocabulary entries (list of dicts with
                original, correction, enabled keys).
            on_add: Callback when a new entry is added (original, correction).
            on_remove: Callback when an entry is removed (original).
            on_toggle: Callback when entry enabled state changes (original, enabled).
            on_save: Callback when save is clicked (receives all entries).
        """
        self._t = t
        self._entries: list[dict[str, object]] = entries or []
        self._on_add = on_add
        self._on_remove = on_remove
        self._on_toggle = on_toggle
        self._on_save = on_save

        self._vocab_list: ft.Column = ft.Column()
        self._original_field: ft.TextField = ft.TextField()
        self._correction_field: ft.TextField = ft.TextField()

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the vocabulary editor UI.

        Returns:
            A Flet container with the vocabulary list and add form.
        """
        self._original_field = ft.TextField(
            hint_text=self._t.get("vocab.original"),
            border_color=Colors.BORDER_DARK,
            text_size=Typography.SIZE_SM,
            width=200,
        )
        self._correction_field = ft.TextField(
            hint_text=self._t.get("vocab.correction"),
            border_color=Colors.BORDER_DARK,
            text_size=Typography.SIZE_SM,
            width=200,
        )

        add_btn = ft.ElevatedButton(
            content=ft.Text(self._t.get("vocab.add")),
            icon=ft.Icons.ADD,
            bgcolor=Colors.PRIMARY_DARK,
            color=Colors.TEXT_PRIMARY_DARK,
            on_click=self._on_add_click,
        )
        save_btn = ft.ElevatedButton(
            content=ft.Text(self._t.get("vocab.save")),
            icon=ft.Icons.SAVE,
            bgcolor=Colors.SUCCESS,
            color=Colors.TEXT_PRIMARY_DARK,
            on_click=self._on_save_click,
        )

        self._vocab_list = ft.Column(
            controls=self._build_entry_rows(),
            spacing=Spacing.SM,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("vocab.title"),
                        size=Typography.SIZE_LG,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Text(
                        value=self._t.get("vocab.description"),
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Row(
                        controls=[
                            self._original_field,
                            self._correction_field,
                            add_btn,
                        ],
                        spacing=Spacing.SM,
                    ),
                    ft.Divider(color=Colors.BORDER_DARK),
                    self._vocab_list,
                    ft.Row(
                        controls=[save_btn],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=Spacing.MD,
            ),
            padding=Spacing.MD,
        )

    # ------------------------------------------------------------------
    # Entry building
    # ------------------------------------------------------------------

    def _build_entry_rows(self) -> list[ft.Control]:
        """Build row controls for each vocabulary entry.

        Returns:
            List of Flet Row controls.
        """
        rows: list[ft.Control] = []
        for entry in self._entries:
            original = str(entry.get("original", ""))
            correction = str(entry.get("correction", ""))
            enabled = bool(entry.get("enabled", True))

            rows.append(
                ft.Row(
                    controls=[
                        ft.Switch(
                            value=enabled,
                            on_change=lambda e, orig=original: self._on_toggle_entry(
                                orig, e.control.value
                            ),
                        ),
                        ft.Text(
                            value=f"{original} → {correction}",
                            size=Typography.SIZE_MD,
                            color=Colors.TEXT_PRIMARY_DARK
                            if enabled
                            else Colors.TEXT_SECONDARY_DARK,
                            font_family=Typography.FONT_FAMILY,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=18,
                            tooltip=self._t.get("vocab.remove"),
                            on_click=lambda e, orig=original: self._on_remove_entry(
                                orig
                            ),
                        ),
                    ],
                    spacing=Spacing.SM,
                )
            )

        if not rows:
            rows.append(
                ft.Text(
                    value=self._t.get("vocab.empty"),
                    size=Typography.SIZE_MD,
                    color=Colors.TEXT_SECONDARY_DARK,
                    font_family=Typography.FONT_FAMILY,
                    italic=True,
                )
            )

        return rows

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_add_click(self, e: ft.ControlEvent) -> None:
        """Handle add entry button click.

        Args:
            e: Flet control event.
        """
        original = (self._original_field.value or "").strip()
        correction = (self._correction_field.value or "").strip()

        if not original or not correction:
            return

        # Add to internal list
        self._entries.append(
            {"original": original, "correction": correction, "enabled": True}
        )

        # Clear form
        self._original_field.value = ""
        self._correction_field.value = ""

        # Refresh display
        self._vocab_list.controls = self._build_entry_rows()

        if self._on_add:
            self._on_add(original, correction)
        self.update()

    def _on_remove_entry(self, original: str) -> None:
        """Handle entry removal.

        Args:
            original: The original word to remove.
        """
        self._entries = [
            e for e in self._entries if str(e.get("original")) != original
        ]
        self._vocab_list.controls = self._build_entry_rows()
        if self._on_remove:
            self._on_remove(original)
        self.update()

    def _on_toggle_entry(self, original: str, enabled: bool) -> None:
        """Handle entry enable/disable toggle.

        Args:
            original: The original word.
            enabled: New enabled state.
        """
        for entry in self._entries:
            if str(entry.get("original")) == original:
                entry["enabled"] = enabled
                break
        self._vocab_list.controls = self._build_entry_rows()
        if self._on_toggle:
            self._on_toggle(original, enabled)
        self.update()

    def _on_save_click(self, e: ft.ControlEvent) -> None:
        """Handle save button click.

        Args:
            e: Flet control event.
        """
        if self._on_save:
            self._on_save(list(self._entries))
