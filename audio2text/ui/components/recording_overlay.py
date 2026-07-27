"""@File: audio2text/ui/components/recording_overlay.py
@Description: Floating overlay displayed during recording with LED indicator and countdown.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.state.store import AppState, RecordingState
from audio2text.ui.theme.theme import Colors, Spacing, Typography


class RecordingOverlay(ft.Column):
    """Semi-transparent overlay shown during active recording.

    Displays:
    - Pulsing LED indicator for recording state.
    - Countdown/elapsed timer.
    - Cancel and stop buttons.
    """

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
        on_cancel: ft.OptionalEventCallable = None,
        on_stop: ft.OptionalEventCallable = None,
    ) -> None:
        """Initialize the recording overlay.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
            on_cancel: Callback when recording is cancelled.
            on_stop: Callback when recording is stopped (finish).
        """
        self._store = store
        self._t = t
        self._on_cancel = on_cancel
        self._on_stop = on_stop

        self._led: ft.Icon = ft.Icon(icon=ft.Icons.CIRCLE)
        self._timer: ft.Text = ft.Text()
        self._visible: bool = False

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the recording overlay UI.

        Returns:
            A Flet Stack with the overlay content.
        """
        self._led = ft.Icon(
            icon=ft.Icons.CIRCLE,
            size=16,
            color=Colors.LED_RECORDING,
        )
        self._timer = ft.Text(
            value="00:00",
            size=Typography.SIZE_XL,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_PRIMARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

        state_label = ft.Text(
            value=self._t.get("overlay.recording"),
            size=Typography.SIZE_MD,
            color=Colors.TEXT_PRIMARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

        cancel_btn = ft.ElevatedButton(
            content=ft.Text(self._t.get("overlay.cancel")),
            icon=ft.Icons.CANCEL,
            bgcolor=Colors.ERROR,
            color=Colors.TEXT_PRIMARY_DARK,
            on_click=self._on_cancel,
        )
        stop_btn = ft.ElevatedButton(
            content=ft.Text(self._t.get("overlay.stop")),
            icon=ft.Icons.STOP,
            bgcolor=Colors.PRIMARY_DARK,
            color=Colors.TEXT_PRIMARY_DARK,
            on_click=self._on_stop,
        )

        return ft.Container(
            visible=False,
            bgcolor=Colors.OVERLAY_BG,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self._led, state_label],
                        spacing=Spacing.SM,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self._timer,
                    ft.Row(
                        controls=[cancel_btn, stop_btn],
                        spacing=Spacing.LG,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Spacing.LG,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.Alignment.CENTER,
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
        """Show/hide overlay based on recording state.

        Args:
            state: New recording state.
        """
        show = state in (RecordingState.RECORDING, RecordingState.PAUSED)
        self._visible = show
        self.visible = show
        if state == RecordingState.PAUSED:
            self._led.color = Colors.LED_PAUSED
        else:
            self._led.color = Colors.LED_RECORDING
        self._safe_update()

    def _on_timer_tick(self, elapsed_s: float) -> None:
        """Update the elapsed timer display.

        Args:
            elapsed_s: Elapsed recording time in seconds.
        """
        minutes = int(elapsed_s // 60)
        seconds = int(elapsed_s % 60)
        self._timer.value = f"{minutes:02d}:{seconds:02d}"
        self._safe_update()

    def _safe_update(self) -> None:
        """Update the control, swallowing errors when not attached to a page."""
        try:
            self.update()
        except RuntimeError:
            pass
