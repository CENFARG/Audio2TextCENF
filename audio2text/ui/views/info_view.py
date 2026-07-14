"""@File: audio2text/ui/views/info_view.py
@Description: Information/About view — shows app version, credits, license, and system info.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
import platform
import sys

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Colors, Spacing, Typography

_logger = logging.getLogger("ui.views.info_view")


class InfoView(ft.Column):
    """About/Information view — app version, credits, license, system details."""

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
    ) -> None:
        """Initialize the info view.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
        """
        _logger.info("InfoView.__init__ — building")
        self._store = store
        self._t = t

        self._version_text: ft.Text = ft.Text()
        self._credits_text: ft.Text = ft.Text()
        self._license_text: ft.Text = ft.Text()
        self._python_text: ft.Text = ft.Text()
        self._platform_text: ft.Text = ft.Text()

        ui = self.build()
        super().__init__(controls=[ui], expand=True)
        _logger.info("InfoView.__init__ — built with %d control(s)", len(self.controls))

    def build(self) -> ft.Control:
        """Build the info view UI.

        Returns:
            A Flet container with app info.
        """
        _logger.info("InfoView.build() — rendering UI")

        self._version_text = ft.Text(
            value=self._t.get("info.app_version"),
            size=Typography.SIZE_XL,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_PRIMARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )
        self._credits_text = ft.Text(
            value=self._t.get("info.credits"),
            size=Typography.SIZE_MD,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )
        self._license_text = ft.Text(
            value=self._t.get("info.license"),
            size=Typography.SIZE_MD,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )
        self._python_text = ft.Text(
            value=self._t.get("info.python_version", version=sys.version.split()[0]),
            size=Typography.SIZE_MD,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )
        self._platform_text = ft.Text(
            value=self._t.get("info.platform", platform=platform.platform()),
            size=Typography.SIZE_MD,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

        close_btn = ft.ElevatedButton(
            content=ft.Text(self._t.get("info.close")),
            icon=ft.Icons.CLOSE,
            bgcolor=Colors.PRIMARY_DARK,
            color=Colors.TEXT_PRIMARY_DARK,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("info.title"),
                        size=Typography.SIZE_XL,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Divider(color=Colors.BORDER_DARK),
                    self._version_text,
                    self._credits_text,
                    self._license_text,
                    ft.Divider(color=Colors.BORDER_DARK),
                    ft.Text(
                        value=self._t.get("info.system_info"),
                        size=Typography.SIZE_LG,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    self._python_text,
                    self._platform_text,
                    ft.Container(
                        content=close_btn,
                        alignment=ft.alignment.Alignment.CENTER,
                        padding=ft.Padding.only(top=Spacing.LG),
                    ),
                ],
                spacing=Spacing.MD,
                expand=True,
            ),
            padding=Spacing.XL,
            expand=True,
            bgcolor=Colors.BACKGROUND_DARK,
        )
