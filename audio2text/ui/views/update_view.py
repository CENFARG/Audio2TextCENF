"""@File: audio2text/ui/views/update_view.py
@Description: Update view — check for updates, download progress, version status.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.client.api_client import APIClient
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Colors, Spacing, Typography

_logger = logging.getLogger("ui.views.update_view")


class UpdateView(ft.Column):
    """Update check and download view."""

    def __init__(
        self,
        store: AppState,
        api: APIClient,
        t: LocalizationManager,
    ) -> None:
        """Initialize the update view.

        Args:
            store: Central application state.
            api: API client for backend communication.
            t: Localization manager for translated strings.
        """
        _logger.info("UpdateView.__init__ — building")
        self._store = store
        self._api = api
        self._t = t

        self._check_button: ft.ElevatedButton = ft.ElevatedButton()
        self._status_text: ft.Text = ft.Text()
        self._progress_bar: ft.ProgressBar = ft.ProgressBar()
        self._current_version_text: ft.Text = ft.Text()
        self._loading_spinner: ft.ProgressRing = ft.ProgressRing()

        ui = self.build()
        super().__init__(controls=[ui], expand=True)
        _logger.info("UpdateView.__init__ — built with %d control(s)", len(self.controls))

    def build(self) -> ft.Control:
        """Build the update view UI.

        Returns:
            A Flet container with update controls.
        """
        _logger.info("UpdateView.build() — rendering UI")

        self._check_button = ft.ElevatedButton(
            content=ft.Text(self._t.get("update.check")),
            icon=ft.Icons.SYSTEM_UPDATE,
            bgcolor=Colors.PRIMARY_DARK,
            color=Colors.TEXT_PRIMARY_DARK,
            on_click=self._on_check_click,
        )
        self._status_text = ft.Text(
            value="",
            size=Typography.SIZE_MD,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )
        self._progress_bar = ft.ProgressBar(
            width=300,
            visible=False,
            color=Colors.PRIMARY_DARK,
        )
        self._current_version_text = ft.Text(
            value=self._t.get("update.current_version", version="0.16.0"),
            size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )
        self._loading_spinner = ft.ProgressRing(
            width=24,
            height=24,
            visible=False,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("update.title"),
                        size=Typography.SIZE_XL,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Divider(color=Colors.BORDER_DARK),
                    self._current_version_text,
                    ft.Row(
                        controls=[
                            self._check_button,
                            self._loading_spinner,
                        ],
                        spacing=Spacing.MD,
                    ),
                    self._status_text,
                    self._progress_bar,
                ],
                spacing=Spacing.MD,
                expand=True,
            ),
            padding=Spacing.XL,
            expand=True,
            bgcolor=Colors.BACKGROUND_DARK,
        )

    def _on_check_click(self, e: ft.ControlEvent) -> None:
        """Handle check-for-updates button click.

        Args:
            e: Flet control event.
        """
        self._loading_spinner.visible = True
        self._status_text.value = self._t.get("update.checking")
        self._check_button.disabled = True
        self.update()

        page = self._get_page()
        if page is not None:
            page.run_task(self._do_check_for_updates)

    async def _do_check_for_updates(self) -> None:
        """Call the API asynchronously to check for updates and display results."""
        try:
            result = await self._api.check_for_updates()
        except Exception as exc:
            self._loading_spinner.visible = False
            self._check_button.disabled = False
            self._status_text.value = str(exc)
            self._status_text.color = Colors.ERROR
            self.update()
            return

        self._loading_spinner.visible = False
        self._check_button.disabled = False

        has_update = bool(result.get("has_update", False))
        if has_update:
            latest = result.get("latest_version", "")
            self._status_text.value = self._t.get(
                "update.available", version=latest
            )
            self._status_text.color = Colors.SUCCESS
        else:
            self._status_text.value = self._t.get("update.up_to_date")
            self._status_text.color = Colors.SUCCESS
        self.update()

    def _get_page(self) -> ft.Page | None:
        """Return the current page reference, handling test contexts."""
        try:
            return self.page
        except RuntimeError:
            return None
