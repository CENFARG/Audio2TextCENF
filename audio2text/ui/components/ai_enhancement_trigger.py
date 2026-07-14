"""@File: audio2text/ui/components/ai_enhancement_trigger.py
@Description: AI enhancement button with profile selector (light/medium/aggressive)
    and loading state for triggering AI text polishing.
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

_PROFILE_OPTIONS = [
    ("light", "enhance.profile_light"),
    ("medium", "enhance.profile_medium"),
    ("aggressive", "enhance.profile_aggressive"),
]


class AIEnhancementTrigger(ft.Column):
    """Button + profile selector to trigger AI enhancement.

    Features:
    - Dropdown to select enhancement profile.
    - "Enhance" button with loading spinner.
    - Result display area showing enhanced text.
    """

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
        on_enhance: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the AI enhancement trigger.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
            on_enhance: Callback when enhance is triggered (receives profile).
        """
        self._store = store
        self._t = t
        self._on_enhance = on_enhance

        self._profile_dropdown: ft.Dropdown = ft.Dropdown()
        self._enhance_button: ft.ElevatedButton = ft.ElevatedButton()
        self._loading_spinner: ft.ProgressRing = ft.ProgressRing()
        self._status_text: ft.Text = ft.Text()

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the AI enhancement trigger UI.

        Returns:
            A Flet container with controls.
        """
        self._profile_dropdown = ft.Dropdown(
            label=self._t.get("enhance.profile"),
            options=[
                ft.dropdown.Option(
                    key=profile_id,
                    text=self._t.get(label_key),
                )
                for profile_id, label_key in _PROFILE_OPTIONS
            ],
            value=self._store.enhancement_profile,
            on_select=self._on_profile_change,
            width=180,
            text_size=Typography.SIZE_SM,
        )
        self._enhance_button = ft.ElevatedButton(
            content=ft.Text(self._t.get("enhance.trigger")),
            icon=ft.Icons.AUTO_AWESOME,
            bgcolor=Colors.SUCCESS,
            color=Colors.TEXT_PRIMARY_DARK,
            on_click=self._on_enhance_click,
        )
        self._loading_spinner = ft.ProgressRing(
            width=24, height=24, visible=False
        )
        self._status_text = ft.Text(
            value="",
            size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("enhance.title"),
                        size=Typography.SIZE_LG,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Text(
                        value=self._t.get("enhance.description"),
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Row(
                        controls=[
                            self._profile_dropdown,
                            self._enhance_button,
                            self._loading_spinner,
                        ],
                        spacing=Spacing.MD,
                    ),
                    self._status_text,
                ],
                spacing=Spacing.MD,
            ),
            padding=Spacing.MD,
        )

    def did_mount(self) -> None:
        """Subscribe to loading state changes."""
        self._store.on_loading_change = self._on_loading_change  # type: ignore[assignment]

    def will_unmount(self) -> None:
        """Unsubscribe from state changes."""
        self._store.on_loading_change = None

    def _on_profile_change(self, e: ft.ControlEvent) -> None:
        """Handle profile dropdown change.

        Args:
            e: Flet control event.
        """
        if e.control.value:
            self._store.enhancement_profile = str(e.control.value)

    def _on_enhance_click(self, e: ft.ControlEvent) -> None:
        """Handle enhance button click.

        Args:
            e: Flet control event.
        """
        if self._on_enhance:
            self._on_enhance(self._store.enhancement_profile)

    def _on_loading_change(self, loading: bool) -> None:
        """Show/hide loading spinner.

        Args:
            loading: Whether enhancement is in progress.
        """
        self._loading_spinner.visible = loading
        self._enhance_button.disabled = loading
        if loading:
            self._status_text.value = self._t.get("enhance.processing")
        self.update()

    def set_result(self, success: bool, message: str = "") -> None:
        """Display enhancement result status.

        Args:
            success: Whether the enhancement succeeded.
            message: Optional status message.
        """
        if success:
            self._status_text.value = self._t.get("enhance.success")
            self._status_text.color = Colors.SUCCESS
        else:
            self._status_text.value = self._t.get(
                "enhance.error", error=message
            )
            self._status_text.color = Colors.ERROR
        self.update()
