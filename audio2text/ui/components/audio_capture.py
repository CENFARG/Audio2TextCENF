"""@File: audio2text/ui/components/audio_capture.py
@Description: Record button with visual feedback for toggle/hold recording modes.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.client.api_client import APIClient
from audio2text.ui.state.store import AppState, RecordingState
from audio2text.ui.theme.theme import Colors, Spacing, Typography


class AudioCapture(ft.Column):
    """Record button component with mode toggle (press-and-hold / toggle).

    Emits recording start/stop actions via the APIClient.
    """

    def __init__(
        self,
        store: AppState,
        api: APIClient,
        t: LocalizationManager,
        on_record_start: Callable[[], None] | None = None,
        on_record_stop: Callable[[], None] | None = None,
        on_stream_start: Callable[[], object] | None = None,
    ) -> None:
        """Initialize the audio capture button.

        Args:
            store: Central application state.
            api: API client for backend communication.
            t: Localization manager for translated strings.
            on_record_start: Callback when recording starts.
            on_record_stop: Callback when recording stops.
            on_stream_start: Async callback to start the full recording+stream flow.
        """
        self._store = store
        self._api = api
        self._t = t
        self._on_record_start = on_record_start
        self._on_record_stop = on_record_stop
        self._on_stream_start = on_stream_start
        self._page: ft.Page | None = None
        self._chunk_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

        self._record_button: ft.IconButton = ft.IconButton(icon=ft.Icons.MIC)

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the audio capture UI.

        Returns:
            A Flet container with the record button and mode indicator.
        """
        is_recording = self._store.recording_state == RecordingState.RECORDING

        self._record_button = ft.IconButton(
            icon=ft.Icons.MIC if not is_recording else ft.Icons.STOP,
            icon_size=40,
            icon_color=Colors.TEXT_PRIMARY_DARK if not is_recording else Colors.ERROR,
            bgcolor=(
                Colors.PRIMARY_DARK if not is_recording else Colors.ERROR + "30"
            ),
            tooltip=self._t.get("capture.start_recording")
            if not is_recording
            else self._t.get("capture.stop_recording"),
            on_click=self._on_click,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    self._record_button,
                    ft.Text(
                        value=self._t.get("capture.press_to_record"),
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Spacing.SM,
            ),
            padding=Spacing.LG,
        )

    def did_mount(self) -> None:
        """Subscribe to recording state changes and capture page reference."""
        self._store.on_recording_state_change = self._on_state_change  # type: ignore[assignment]
        self._page = self.page

    def will_unmount(self) -> None:
        """Unsubscribe from state changes."""
        self._store.on_recording_state_change = None
        self._page = None

    def _get_page(self) -> ft.Page | None:
        """Get the page reference, trying self._page then self.page (safe)."""
        if self._page is not None:
            return self._page
        try:
            return self.page
        except RuntimeError:
            return None

    def _on_click(self, e: ft.ControlEvent) -> None:
        """Handle record button click — start/stop streaming recording via API."""
        page = self._get_page()
        if page is None:
            return

        if self._store.recording_state == RecordingState.RECORDING:
            self._store.recording_state = RecordingState.IDLE
            page.run_task(self._api.stop_recording)
        else:
            self._store.recording_state = RecordingState.RECORDING
            if self._on_stream_start is not None:
                page.run_task(self._on_stream_start)
            else:
                page.run_task(self._api.start_recording)

    def _on_state_change(self, state: RecordingState) -> None:
        """Update button appearance based on recording state.

        Args:
            state: New recording state.
        """
        if state == RecordingState.RECORDING:
            self._record_button.icon = ft.Icons.STOP
            self._record_button.icon_color = Colors.ERROR
            self._record_button.bgcolor = Colors.ERROR + "30"
            self._record_button.tooltip = self._t.get("capture.stop_recording")
        else:
            self._record_button.icon = ft.Icons.MIC
            self._record_button.icon_color = Colors.TEXT_PRIMARY_DARK
            self._record_button.bgcolor = Colors.PRIMARY_DARK
            self._record_button.tooltip = self._t.get("capture.start_recording")
        self.update()

    # ------------------------------------------------------------------
    # Audio chunk capture (async generator)
    # ------------------------------------------------------------------

    async def capture_chunks(self) -> AsyncIterator[bytes]:
        """Yield audio bytes from the internal chunk queue.

        Stops when a None sentinel is encountered.
        """
        while True:
            chunk = await self._chunk_queue.get()
            if chunk is None:
                break
            yield chunk
