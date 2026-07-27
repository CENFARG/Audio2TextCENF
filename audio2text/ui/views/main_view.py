"""@File: audio2text/ui/views/main_view.py
@Description: Main app shell with navigation (sidebar tabs), language toggle, and view switching.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.client.api_client import APIClient
from audio2text.ui.components.language_select import LanguageSelect
from audio2text.ui.state.store import AppState, ViewName
from audio2text.ui.theme.theme import Colors, Spacing, Typography
from audio2text.ui.views.history_view import HistoryView
from audio2text.ui.views.info_view import InfoView
from audio2text.ui.views.settings_view import SettingsView
from audio2text.ui.views.transcribe_view import TranscribeView
from audio2text.ui.views.update_view import UpdateView

_logger = logging.getLogger("ui.views.main_view")


class MainView(ft.Column):
    """Root application view with sidebar navigation and view routing."""

    def __init__(
        self,
        page: ft.Page,
        store: AppState,
        api: APIClient,
        t: LocalizationManager,
    ) -> None:
        """Initialize the main view.

        Args:
            page: Flet page reference.
            store: Central application state.
            api: API client for backend communication.
            t: Localization manager for translated strings.
        """
        self._page = page
        self._store = store
        self._api = api
        self._t = t

        # Views
        self._transcribe_view = TranscribeView(store=store, api=api, t=t)
        self._history_view = HistoryView(store=store, api=api, t=t)
        self._settings_view = SettingsView(store=store, api=api, t=t)
        self._info_view = InfoView(store=store, t=t)
        self._update_view = UpdateView(store=store, api=api, t=t)

        # Navigation (placeholders, build() will replace them)
        self._nav_rail: ft.NavigationRail = ft.NavigationRail()
        self._content_area: ft.Stack = ft.Stack()

        # Position all views to fill the Stack.
        # In Flet, ``expand`` only applies inside Row/Column (flex parents).
        # Inside Stack (absolute positioning), children sit at (0,0) at their
        # intrinsic size. Setting all four edges to 0 makes each view fill the
        # entire Stack — the visibility toggling pattern then shows one at a time.
        for _v in (
            self._transcribe_view,
            self._history_view,
            self._settings_view,
            self._info_view,
            self._update_view,
        ):
            _v.left = 0
            _v.right = 0
            _v.top = 0
            _v.bottom = 0

        # Set initial visibility — only TRANSCRIBE visible by default
        self._transcribe_view.visible = True
        self._history_view.visible = False
        self._settings_view.visible = False
        self._info_view.visible = False
        self._update_view.visible = False

        # Build UI and set controls
        ui = self.build()
        super().__init__(controls=ui.controls, expand=True)

    def build(self) -> ft.Control:
        """Build the main view shell.

        Returns:
            A Flet Row with sidebar and content area.
        """
        # ── Header ──────────────────────────────────────────────────
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        value=self._t.get("app.title"),
                        size=Typography.SIZE_XL,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Row(
                        controls=[
                            LanguageSelect(store=self._store, t=self._t),
                        ],
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.symmetric(
                horizontal=Spacing.MD, vertical=Spacing.SM
            ),
        )

        # ── Navigation Rail ─────────────────────────────────────────
        self._nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=80,
            min_extended_width=160,
            leading=ft.IconButton(
                icon=ft.Icons.MENU,
                on_click=lambda e: self._page.show_dialog(
                    ft.AlertDialog(
                        title=ft.Text(self._t.get("app.about_title")),
                        content=ft.Text(self._t.get("app.about_text")),
                    )
                ),
            ),
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.MIC,
                    selected_icon=ft.Icons.MIC,
                    label=self._t.get("nav.transcribe"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.HISTORY,
                    selected_icon=ft.Icons.HISTORY,
                    label=self._t.get("nav.history"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS,
                    selected_icon=ft.Icons.SETTINGS,
                    label=self._t.get("nav.settings"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INFO,
                    selected_icon=ft.Icons.INFO,
                    label=self._t.get("nav.info"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SYSTEM_UPDATE,
                    selected_icon=ft.Icons.SYSTEM_UPDATE,
                    label=self._t.get("nav.update"),
                ),
            ],
            on_change=self._on_nav_change,
            bgcolor=Colors.SURFACE_DARK,
        )

        # ── Content area (Stack with visibility toggling) ──────────
        # All views are added to the Stack at construction time.
        # View switching toggles .visible instead of replacing .content,
        # which avoids the "Control must be added to the page first" crash
        # when swapping complex custom controls in Flet.
        self._content_area = ft.Stack(
            controls=[
                self._transcribe_view,
                self._history_view,
                self._settings_view,
                self._info_view,
                self._update_view,
            ],
            expand=True,
        )

        # ── Status bar ──────────────────────────────────────────────
        status_text = ft.Text(
            value="Audio2Text CENF v0.16.0",
            size=Typography.SIZE_XS,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

        return ft.Column(
            controls=[
                header,
                ft.Row(
                    controls=[
                        self._nav_rail,
                        ft.VerticalDivider(width=1, color=Colors.BORDER_DARK),
                        self._content_area,
                    ],
                    expand=True,
                ),
                ft.Container(
                    content=status_text,
                    padding=ft.Padding.symmetric(
                        horizontal=Spacing.SM, vertical=Spacing.XS
                    ),
                    bgcolor=Colors.SURFACE_DARK,
                ),
            ],
            expand=True,
        )

    def did_mount(self) -> None:
        """Subscribe to view changes."""
        self._store.on_view_change = self._on_view_changed  # type: ignore[assignment]

    def will_unmount(self) -> None:
        """Unsubscribe from state changes."""
        self._store.on_view_change = None

    def _on_nav_change(self, e: ft.ControlEvent) -> None:
        """Handle navigation rail selection.

        Args:
            e: Flet control event.
        """
        index = int(e.control.selected_index) if e.control.selected_index is not None else 0
        view_map = {
            0: ViewName.TRANSCRIBE,
            1: ViewName.HISTORY,
            2: ViewName.SETTINGS,
            3: ViewName.INFO,
            4: ViewName.UPDATE,
        }
        self._store.current_view = view_map.get(index, ViewName.TRANSCRIBE)

    def _on_view_changed(self, view: ViewName) -> None:
        """Toggle visibility of views in the Stack to show the active view.

        Uses the recommended Flet routing pattern: all views live in a
        ft.Stack, and view switching toggles their ``visible`` property
        followed by ``page.update()``. This avoids the RuntimeError
        that occurs when swapping ``Container.content`` with complex
        custom controls that lose their ``.page`` reference.

        Args:
            view: New active view name.
        """
        view_map: dict[ViewName, ft.Control] = {
            ViewName.TRANSCRIBE: self._transcribe_view,
            ViewName.HISTORY: self._history_view,
            ViewName.SETTINGS: self._settings_view,
            ViewName.INFO: self._info_view,
            ViewName.UPDATE: self._update_view,
        }
        for vn, ctrl in view_map.items():
            ctrl.visible = (vn == view)
        self._page.update()
