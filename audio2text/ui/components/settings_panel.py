"""@File: audio2text/ui/components/settings_panel.py
@Description: Settings tab container that holds all settings sub-panels.
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


class SettingsPanel(ft.Column):
    """Container for all settings sub-panels with tabs."""

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
        children: list[ft.Control] | None = None,
        on_save: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the settings panel.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
            children: List of settings sub-panel controls.
            on_save: Callback when save button is clicked.
        """
        self._store = store
        self._t = t
        self._children = children or []
        self._on_save = on_save

        ui = self.build()
        super().__init__(controls=[ui], expand=True)

    def build(self) -> ft.Control:
        """Build the settings panel UI.

        Returns:
            A Flet container with tabs for settings categories.
        """
        providers_content = ft.Column(
            controls=[
                c for c in self._children if hasattr(c, "_radio_group")
            ],
            spacing=Spacing.MD,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        hotkeys_content = ft.Column(
            controls=[
                c for c in self._children if hasattr(c, "_modifier_dropdown")
            ],
            spacing=Spacing.MD,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        vocab_content = ft.Column(
            controls=[
                c for c in self._children if hasattr(c, "_vocab_list")
            ],
            spacing=Spacing.MD,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        tabs = ft.Tabs(
            content=ft.Column([
                ft.TabBar(
                    tabs=[
                        ft.Tab(
                            label=self._t.get("settings.tab_providers"),
                            icon=ft.Icons.SETTINGS_VOICE,
                        ),
                        ft.Tab(
                            label=self._t.get("settings.tab_hotkeys"),
                            icon=ft.Icons.KEYBOARD,
                        ),
                        ft.Tab(
                            label=self._t.get("settings.tab_vocabulary"),
                            icon=ft.Icons.BOOK,
                        ),
                    ],
                ),
                ft.TabBarView(
                    controls=[
                        providers_content,
                        hotkeys_content,
                        vocab_content,
                    ],
                    expand=True,
                ),
            ], expand=True),
            length=3,
            expand=1,
        )

        save_btn = ft.ElevatedButton(
            content=ft.Text(self._t.get("settings.save")),
            icon=ft.Icons.SAVE,
            bgcolor=Colors.PRIMARY_DARK,
            color=Colors.TEXT_PRIMARY_DARK,
            on_click=lambda e: self._on_save and self._on_save(),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("settings.title"),
                        size=Typography.SIZE_XL,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    tabs,
                    ft.Row(
                        controls=[save_btn],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=Spacing.MD,
                expand=True,
            ),
            padding=Spacing.MD,
            expand=True,
        )
