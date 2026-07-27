"""@File: audio2text/ui/components/transcription_panel.py
@Description: Live + final transcription display area with copy and save buttons.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Colors, Spacing, Typography


class TranscriptionPanel(ft.Column):
    """Text display area showing the current/live transcription.

    Features:
    - Scrollable text area for transcription output.
    - Copy to clipboard button.
    - Character count indicator.
    """

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
        on_copy: Callable[[str], None] | None = None,
        on_clear: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the transcription panel.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
            on_copy: Callback when copy is requested (receives the text).
            on_clear: Callback when clear is requested.
        """
        self._store = store
        self._t = t
        self._on_copy = on_copy
        self._on_clear = on_clear

        self._text_display: ft.TextField = ft.TextField()
        self._char_count: ft.Text = ft.Text()

        ui = self.build()
        super().__init__(controls=[ui], expand=True)

    def build(self) -> ft.Control:
        """Build the transcription panel UI.

        Returns:
            A Flet container with the text area and action buttons.
        """
        self._text_display = ft.TextField(
            value=self._store.current_transcription_text or "",
            multiline=True,
            min_lines=10,
            expand=True,
            read_only=True,
            text_size=Typography.SIZE_MD,
            border_color=Colors.BORDER_DARK,
            content_padding=Spacing.MD,
            hint_text=self._t.get("transcription.hint"),
            hint_style=ft.TextStyle(
                color=Colors.TEXT_SECONDARY_DARK,
                font_family=Typography.FONT_FAMILY,
            ),
        )
        text_len = len(self._store.current_transcription_text)
        self._char_count = ft.Text(
            value=self._t.get("transcription.chars", count=text_len),
            size=Typography.SIZE_XS,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

        copy_btn = ft.TextButton(
            content=ft.Text(self._t.get("transcription.copy")),
            icon=ft.Icons.CONTENT_COPY,
            on_click=self._on_copy_click,
        )
        clear_btn = ft.TextButton(
            content=ft.Text(self._t.get("transcription.clear")),
            icon=ft.Icons.CLEAR,
            on_click=self._on_clear_click,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[copy_btn, clear_btn],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    self._text_display,
                    self._char_count,
                ],
                spacing=Spacing.SM,
                expand=True,
            ),
            expand=True,
            padding=Spacing.MD,
        )

    def did_mount(self) -> None:
        """Subscribe to text updates."""
        self._store.on_text_update = self._on_text_update  # type: ignore[assignment]

    def will_unmount(self) -> None:
        """Unsubscribe from text updates."""
        self._store.on_text_update = None

    def _on_text_update(self, text: str) -> None:
        """Update the displayed transcription text.

        Args:
            text: New transcription text.
        """
        self._text_display.value = text or ""
        self._char_count.value = self._t.get(
            "transcription.chars", count=len(text)
        )
        self.update()

    def _on_copy_click(self, e: ft.ControlEvent) -> None:
        """Handle copy button click.

        Args:
            e: Flet control event.
        """
        text = self._store.current_transcription_text
        if text and self._on_copy:
            self._on_copy(text)
        e.page.run_task(e.page.clipboard.set, text)

    def _on_clear_click(self, e: ft.ControlEvent) -> None:
        """Handle clear button click.

        Args:
            e: Flet control event.
        """
        if self._on_clear:
            self._on_clear()
        self._store.current_transcription_text = ""
