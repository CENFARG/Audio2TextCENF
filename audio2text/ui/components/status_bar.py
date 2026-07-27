"""@File: audio2text/ui/components/status_bar.py
@Description: Recording status indicator — shows recording state, timer, and transcription status.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.state.store import AppState, RecordingState
from audio2text.ui.theme.theme import Colors, Spacing, Typography


class StatusBar(ft.Column):
    """Bottom status bar showing recording state and elapsed time.

    Displays different colors and icons based on the current
    ``RecordingState`` (idle, recording, paused, processing).
    """

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
    ) -> None:
        """Initialize the status bar.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
        """
        self._store = store
        self._t = t

        # Controls built in build()
        self._status_icon: ft.Icon = ft.Icon(icon=ft.Icons.CIRCLE)
        self._status_text: ft.Text = ft.Text()
        self._timer_text: ft.Text = ft.Text()

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the status bar UI.

        Returns:
            A Flet Row containing the status indicator.
        """
        self._status_icon = ft.Icon(
            icon=ft.Icons.CIRCLE,
            size=Typography.SIZE_SM,
            color=Colors.LED_IDLE,
        )
        self._status_text = ft.Text(
            value=self._t.get("status.idle"),
            size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )
        self._timer_text = ft.Text(
            value="00:00",
            size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[self._status_icon, self._status_text],
                        spacing=Spacing.XS,
                    ),
                    self._timer_text,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.symmetric(
                horizontal=Spacing.MD, vertical=Spacing.SM
            ),
            bgcolor=Colors.SURFACE_DARK,
        )

    def did_mount(self) -> None:
        """Subscribe to recording state changes."""
        self._store.on_recording_state_change = self._on_state_change  # type: ignore[assignment]
        self._store.on_timer_tick = self._on_timer_tick  # type: ignore[assignment]

    def will_unmount(self) -> None:
        """Unsubscribe from state changes."""
        self._store.on_recording_state_change = None
        self._store.on_timer_tick = None

    def _on_state_change(self, state: RecordingState) -> None:
        """Update status bar based on recording state.

        Args:
            state: New recording state.
        """
        color_map = {
            RecordingState.IDLE: Colors.LED_IDLE,
            RecordingState.RECORDING: Colors.LED_RECORDING,
            RecordingState.PAUSED: Colors.LED_PAUSED,
            RecordingState.PROCESSING: Colors.LED_PAUSED,
        }
        text_map = {
            RecordingState.IDLE: self._t.get("status.idle"),
            RecordingState.RECORDING: self._t.get("status.recording"),
            RecordingState.PAUSED: self._t.get("status.paused"),
            RecordingState.PROCESSING: self._t.get("status.processing"),
        }

        self._status_icon.color = color_map.get(state, Colors.LED_IDLE)
        self._status_text.value = text_map.get(state, self._t.get("status.idle"))
        self.update()

    def _on_timer_tick(self, elapsed_s: float) -> None:
        """Update the elapsed timer display.

        Args:
            elapsed_s: Elapsed recording time in seconds.
        """
        minutes = int(elapsed_s // 60)
        seconds = int(elapsed_s % 60)
        self._timer_text.value = f"{minutes:02d}:{seconds:02d}"
        self.update()
