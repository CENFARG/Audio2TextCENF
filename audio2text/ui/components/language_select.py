"""@File: audio2text/ui/components/language_select.py
@Description: Language dropdown selector for UI language (es/en).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Spacing, Typography

_LANGUAGE_OPTIONS = [
    ("es", "Español"),
    ("en", "English"),
]


class LanguageSelect(ft.Column):
    """Simple dropdown to switch UI language."""

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
    ) -> None:
        """Initialize the language selector.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
        """
        self._store = store
        self._t = t
        self._dropdown: ft.Dropdown = ft.Dropdown()

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the language selector UI.

        Returns:
            A Flet dropdown control.
        """
        self._dropdown = ft.Dropdown(
            label=self._t.get("settings.language"),
            options=[
                ft.dropdown.Option(key=code, text=label)
                for code, label in _LANGUAGE_OPTIONS
            ],
            value=self._store.current_language,
            on_select=self._on_change,
            width=140,
            text_size=Typography.SIZE_SM,
        )

        return ft.Container(
            content=self._dropdown,
            padding=ft.Padding.only(right=Spacing.MD),
        )

    def _on_change(self, e: ft.ControlEvent) -> None:
        """Handle language selection.

        Args:
            e: Flet control event.
        """
        new_lang = str(e.control.value) if e.control.value else "es"
        self._store.current_language = new_lang
        self._t.set_language(new_lang)
