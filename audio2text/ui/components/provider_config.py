"""@File: audio2text/ui/components/provider_config.py
@Description: Transcription provider selector — radio buttons for Groq, faster-whisper, NVIDIA.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Colors, Spacing, Typography

_PROVIDER_OPTIONS = [
    ("groq", "providers.groq"),
    ("faster_whisper", "providers.faster_whisper"),
    ("nvidia_riva", "providers.nvidia_riva"),
]


class ProviderConfig(ft.Column):
    """Radio group to select the active transcription provider."""

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
    ) -> None:
        """Initialize the provider configuration component.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
        """
        self._store = store
        self._t = t
        self._radio_group: ft.RadioGroup | None = None

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the provider selector UI.

        Returns:
            A Flet container with radio buttons.
        """
        radios: list[ft.Radio] = []
        for provider_id, label_key in _PROVIDER_OPTIONS:
            radios.append(
                ft.Radio(
                    value=provider_id,
                    label=self._t.get(label_key),
                )
            )

        self._radio_group = ft.RadioGroup(
            value=self._store.selected_provider,
            content=ft.Column(controls=radios, spacing=Spacing.SM),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("settings.provider"),
                        size=Typography.SIZE_LG,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Text(
                        value=self._t.get("settings.provider_desc"),
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    self._radio_group,
                ],
                spacing=Spacing.MD,
            ),
            padding=Spacing.MD,
        )

    def did_mount(self) -> None:
        """Subscribe to provider changes."""
        self._store.on_provider_change = self._on_provider_change  # type: ignore[assignment]
        self._radio_group.on_change = self._on_radio_change  # type: ignore[assignment]

    def will_unmount(self) -> None:
        """Unsubscribe from state changes."""
        self._store.on_provider_change = None
        self._radio_group.on_change = None

    def _on_radio_change(self, e: ft.ControlEvent) -> None:
        """Handle radio button selection.

        Args:
            e: Flet control event.
        """
        if e.control.value:
            self._store.selected_provider = str(e.control.value)

    def _on_provider_change(self, provider: str) -> None:
        """Update radio group when provider changes externally.

        Args:
            provider: New provider ID.
        """
        self._radio_group.value = provider
        self.update()
