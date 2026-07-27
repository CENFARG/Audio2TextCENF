"""@File: audio2text/ui/views/transcribe_view.py
@Description: Main transcription view — recording controls + live transcription display.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.client.api_client import APIClient
from audio2text.ui.components.ai_enhancement_trigger import AIEnhancementTrigger
from audio2text.ui.components.audio_capture import AudioCapture
from audio2text.ui.components.context_blocks_selector import ContextBlocksSelector
from audio2text.ui.components.recording_overlay import RecordingOverlay
from audio2text.ui.components.status_bar import StatusBar
from audio2text.ui.components.transcription_panel import TranscriptionPanel
from audio2text.ui.state.store import AppState, RecordingState
from audio2text.ui.theme.theme import Colors, Spacing

_logger = logging.getLogger("ui.views.transcribe_view")


class TranscribeView(ft.Column):
    """Main capture + transcription view with sidebar for context blocks."""

    def __init__(
        self,
        store: AppState,
        api: APIClient,
        t: LocalizationManager,
    ) -> None:
        """Initialize the transcribe view.

        Args:
            store: Central application state.
            api: API client for backend communication.
            t: Localization manager for translated strings.
        """
        _logger.info("TranscribeView.__init__ — building")
        self._store = store
        self._api = api
        self._t = t

        self._transcription_panel = TranscriptionPanel(store=store, t=t)
        self._audio_capture = AudioCapture(
            store=store, api=api, t=t,
            on_stream_start=self._stream_recording,
        )
        self._status_bar = StatusBar(store=store, t=t)
        self._overlay = RecordingOverlay(store=store, t=t)
        self._blocks_selector = ContextBlocksSelector(store=store, api=api, t=t)
        self._enhance_trigger = AIEnhancementTrigger(store=store, t=t)

        ui = self.build()
        super().__init__(controls=[ui], expand=True)
        _logger.info("TranscribeView.__init__ — controls: %d", len(self.controls))

    def build(self) -> ft.Control:
        """Build the transcribe view UI.

        Returns:
            A Flet container with the main recording + transcription layout.
        """
        return ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Column(
                        controls=[
                            # Main content area
                            ft.Row(
                                controls=[
                                    # Center: recording + transcription
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                self._audio_capture,
                                                self._transcription_panel,
                                                self._enhance_trigger,
                                            ],
                                            spacing=Spacing.MD,
                                            expand=True,
                                            scroll=ft.ScrollMode.AUTO,
                                        ),
                                        expand=3,
                                        padding=Spacing.MD,
                                    ),
                                    # Right sidebar: context blocks
                                    ft.Container(
                                        content=self._blocks_selector,
                                        width=280,
                                        bgcolor=Colors.SURFACE_DARK,
                                        padding=Spacing.SM,
                                    ),
                                ],
                                expand=True,
                            ),
                            self._status_bar,
                        ],
                        expand=True,
                    ),
                    # Floating overlay for recording
                    self._overlay,
                ],
                expand=True,
            ),
            expand=True,
            bgcolor=Colors.BACKGROUND_DARK,
        )

    # ------------------------------------------------------------------
    # Streaming integration
    # ------------------------------------------------------------------

    def _on_transcription_chunk(self, text: str) -> None:
        """Append a transcription chunk to the store's current text.

        Args:
            text: Incoming transcription text chunk.
        """
        current = self._store.current_transcription_text
        self._store.current_transcription_text = current + text

    async def _stream_recording(self) -> None:
        """Start recording, stream transcription via WS, stop recording."""
        try:
            await self._api.start_recording()
            await self._api.listen_transcription_stream(
                on_chunk=self._on_transcription_chunk,
                on_error=lambda err: self._api.show_error(
                    None, str(err.get("message", "Stream error")),
                ),
            )
        except Exception as exc:
            self._api.show_error(None, f"Recording failed: {exc}")
        finally:
            try:
                await self._api.stop_recording()
            except Exception:
                pass
            self._store.recording_state = RecordingState.IDLE
