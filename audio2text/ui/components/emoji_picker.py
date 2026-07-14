"""@File: audio2text/ui/components/emoji_picker.py
@Description: Grid-based emoji selector for customizing transcription titles.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.theme.theme import Colors, Spacing, Typography

# Curated emoji set for transcription categorization
_DEFAULT_EMOJIS = [
    "🎙️", "🎧", "🎵", "🎤", "📝", "📋", "📌", "📎",
    "💡", "💬", "💭", "🗣️", "📢", "🔊", "🔔", "✅",
    "⭐", "🔥", "🚀", "⚡", "💻", "🤖", "📊", "📈",
    "🏢", "🏠", "🏥", "📚", "🎓", "💼", "⚖️", "💰",
    "😀", "😊", "🤔", "👍", "👏", "🙌", "❤️", "🎉",
]


class EmojiPicker(ft.Column):
    """A grid of emojis for selecting a title emoji.

    On selection, fires ``on_pick`` with the chosen emoji character.
    """

    def __init__(
        self,
        t: LocalizationManager,
        emojis: list[str] | None = None,
        on_pick: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the emoji picker.

        Args:
            t: Localization manager for translated strings.
            emojis: Custom emoji list (defaults to _DEFAULT_EMOJIS).
            on_pick: Callback when an emoji is selected.
        """
        self._t = t
        self._emojis = emojis or _DEFAULT_EMOJIS
        self._on_pick = on_pick

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the emoji picker grid UI.

        Returns:
            A Flet container with a grid of emoji buttons.
        """
        rows: list[ft.Row] = []
        row_items: list[ft.Control] = []
        per_row = 8

        for emoji in self._emojis:
            row_items.append(
                ft.TextButton(
                    content=ft.Text(emoji),
                    style=ft.ButtonStyle(padding=ft.Padding(4, 2, 4, 2)),
                    on_click=lambda e, em=emoji: self._on_emoji_click(em),
                )
            )
            if len(row_items) >= per_row:
                rows.append(ft.Row(controls=row_items, spacing=Spacing.XS))
                row_items = []
        if row_items:
            rows.append(ft.Row(controls=row_items, spacing=Spacing.XS))

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("emoji.title"),
                        size=Typography.SIZE_MD,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    *rows,
                ],
                spacing=Spacing.SM,
            ),
            padding=Spacing.SM,
            border=ft.Border(
                top=ft.BorderSide(1, Colors.BORDER_DARK),
                bottom=ft.BorderSide(1, Colors.BORDER_DARK),
                left=ft.BorderSide(1, Colors.BORDER_DARK),
                right=ft.BorderSide(1, Colors.BORDER_DARK),
            ),
            border_radius=8,
            bgcolor=Colors.SURFACE_DARK,
        )

    def _on_emoji_click(self, emoji: str) -> None:
        """Handle emoji button click.

        Args:
            emoji: The selected emoji character.
        """
        if self._on_pick:
            self._on_pick(emoji)
