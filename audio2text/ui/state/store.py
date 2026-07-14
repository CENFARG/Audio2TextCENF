"""@File: audio2text/ui/state/store.py
@Description: Central application state store (Observer pattern) for the Flet frontend.
    Components subscribe to state changes via callback properties.
    No external state library required — simple, explicit, Flet-friendly.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum


class ViewName(str, Enum):
    """Names of top-level views in the application."""

    TRANSCRIBE = "transcribe"
    HISTORY = "history"
    SETTINGS = "settings"
    INFO = "info"
    UPDATE = "update"


class RecordingState(str, Enum):
    """Recording state machine states."""

    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    PROCESSING = "processing"


class AppState:
    """Single source of truth for the Flet UI.

    Every public attribute is a property that fires an optional callback
    on change. Components subscribe by assigning to the ``on_*`` callback
    attributes in ``did_mount()`` and unsubscribe in ``will_unmount()``.

    No external state library required.
    """

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Initialize AppState with sensible defaults."""
        # -- Internal storage --
        self._current_view: ViewName = ViewName.TRANSCRIBE
        self._recording_state: RecordingState = RecordingState.IDLE
        self._recording_elapsed_s: float = 0.0
        self._current_transcription_text: str = ""
        self._current_language: str = "es"
        self._selected_provider: str = "groq"
        self._is_dark_mode: bool = True
        self._error_message: str | None = None
        self._is_loading: bool = False
        self._selected_context_blocks: set[str] = set()
        self._enhancement_profile: str = "medium"
        self._settings: dict[str, object] = {}
        self._history: list[dict[str, object]] = []
        self._context_blocks: list[dict[str, object]] = []

        # -- Callback slots (components assign/unassign) --
        self.on_view_change: Callable[[ViewName], None] | None = None
        self.on_recording_state_change: Callable[[RecordingState], None] | None = None
        self.on_timer_tick: Callable[[float], None] | None = None
        self.on_text_update: Callable[[str], None] | None = None
        self.on_language_change: Callable[[str], None] | None = None
        self.on_provider_change: Callable[[str], None] | None = None
        self.on_theme_change: Callable[[bool], None] | None = None
        self.on_error: Callable[[str | None], None] | None = None
        self.on_loading_change: Callable[[bool], None] | None = None
        self.on_settings_change: Callable[[dict[str, object]], None] | None = None
        self.on_history_change: Callable[[list[dict[str, object]]], None] | None = None
        self.on_context_blocks_change: Callable[[list[dict[str, object]]], None] | None = None

    # ------------------------------------------------------------------
    # current_view
    # ------------------------------------------------------------------

    @property
    def current_view(self) -> ViewName:
        """The currently active application view."""
        return self._current_view

    @current_view.setter
    def current_view(self, value: ViewName) -> None:
        if value != self._current_view:
            self._current_view = value
            if self.on_view_change:
                self.on_view_change(value)

    # ------------------------------------------------------------------
    # recording_state
    # ------------------------------------------------------------------

    @property
    def recording_state(self) -> RecordingState:
        """Current recording FSM state."""
        return self._recording_state

    @recording_state.setter
    def recording_state(self, value: RecordingState) -> None:
        if value != self._recording_state:
            self._recording_state = value
            if self.on_recording_state_change:
                self.on_recording_state_change(value)

    # ------------------------------------------------------------------
    # recording_elapsed_s
    # ------------------------------------------------------------------

    @property
    def recording_elapsed_s(self) -> float:
        """Elapsed recording time in seconds."""
        return self._recording_elapsed_s

    @recording_elapsed_s.setter
    def recording_elapsed_s(self, value: float) -> None:
        self._recording_elapsed_s = value
        if self.on_timer_tick:
            self.on_timer_tick(value)

    # ------------------------------------------------------------------
    # current_transcription_text
    # ------------------------------------------------------------------

    @property
    def current_transcription_text(self) -> str:
        """Live transcription text displayed in the UI."""
        return self._current_transcription_text

    @current_transcription_text.setter
    def current_transcription_text(self, value: str) -> None:
        self._current_transcription_text = value
        if self.on_text_update:
            self.on_text_update(value)

    # ------------------------------------------------------------------
    # current_language
    # ------------------------------------------------------------------

    @property
    def current_language(self) -> str:
        """Current UI language code (e.g., 'es', 'en')."""
        return self._current_language

    @current_language.setter
    def current_language(self, value: str) -> None:
        if value != self._current_language:
            self._current_language = value
            if self.on_language_change:
                self.on_language_change(value)

    # ------------------------------------------------------------------
    # selected_provider
    # ------------------------------------------------------------------

    @property
    def selected_provider(self) -> str:
        """Currently selected transcription provider id."""
        return self._selected_provider

    @selected_provider.setter
    def selected_provider(self, value: str) -> None:
        if value != self._selected_provider:
            self._selected_provider = value
            if self.on_provider_change:
                self.on_provider_change(value)

    # ------------------------------------------------------------------
    # is_dark_mode
    # ------------------------------------------------------------------

    @property
    def is_dark_mode(self) -> bool:
        """Whether the UI is in dark mode."""
        return self._is_dark_mode

    @is_dark_mode.setter
    def is_dark_mode(self, value: bool) -> None:
        if value != self._is_dark_mode:
            self._is_dark_mode = value
            if self.on_theme_change:
                self.on_theme_change(value)

    # ------------------------------------------------------------------
    # error_message
    # ------------------------------------------------------------------

    @property
    def error_message(self) -> str | None:
        """Current error message or None if no error."""
        return self._error_message

    @error_message.setter
    def error_message(self, value: str | None) -> None:
        self._error_message = value
        if self.on_error:
            self.on_error(value)

    def clear_error(self) -> None:
        """Convenience: clear the current error message."""
        self.error_message = None

    # ------------------------------------------------------------------
    # is_loading
    # ------------------------------------------------------------------

    @property
    def is_loading(self) -> bool:
        """Whether a loading spinner should be shown."""
        return self._is_loading

    @is_loading.setter
    def is_loading(self, value: bool) -> None:
        if value != self._is_loading:
            self._is_loading = value
            if self.on_loading_change:
                self.on_loading_change(value)

    # ------------------------------------------------------------------
    # selected_context_blocks
    # ------------------------------------------------------------------

    @property
    def selected_context_blocks(self) -> set[str]:
        """Set of currently selected context block IDs."""
        return self._selected_context_blocks

    @selected_context_blocks.setter
    def selected_context_blocks(self, value: set[str]) -> None:
        self._selected_context_blocks = value

    @property
    def context_block_count(self) -> int:
        """Number of currently selected context blocks."""
        return len(self._selected_context_blocks)

    # ------------------------------------------------------------------
    # enhancement_profile
    # ------------------------------------------------------------------

    @property
    def enhancement_profile(self) -> str:
        """Currently selected enhancement profile (light/medium/aggressive)."""
        return self._enhancement_profile

    @enhancement_profile.setter
    def enhancement_profile(self, value: str) -> None:
        self._enhancement_profile = value

    # ------------------------------------------------------------------
    # settings
    # ------------------------------------------------------------------

    @property
    def settings(self) -> dict[str, object]:
        """Full settings dictionary loaded from the backend."""
        return dict(self._settings)

    # ------------------------------------------------------------------
    # history
    # ------------------------------------------------------------------

    @property
    def history(self) -> list[dict[str, object]]:
        """Transcription history list."""
        return list(self._history)

    # ------------------------------------------------------------------
    # context_blocks
    # ------------------------------------------------------------------

    @property
    def context_blocks(self) -> list[dict[str, object]]:
        """Available context blocks loaded from the backend."""
        return list(self._context_blocks)

    # ------------------------------------------------------------------
    # Hydration methods
    # ------------------------------------------------------------------

    def hydrate_settings(self, data: dict[str, object]) -> None:
        """Replace stored settings with new data and fire callback.

        Args:
            data: Full settings dictionary from the backend.
        """
        self._settings = dict(data)
        if self.on_settings_change:
            self.on_settings_change(dict(self._settings))

    def hydrate_history(self, items: list[dict[str, object]]) -> None:
        """Replace stored history with new items and fire callback.

        Args:
            items: List of history item dicts.
        """
        self._history = list(items)
        if self.on_history_change:
            self.on_history_change(list(self._history))

    def hydrate_blocks(self, blocks: list[dict[str, object]]) -> None:
        """Replace stored context blocks with new data and fire callback.

        Args:
            blocks: List of context block dicts.
        """
        self._context_blocks = list(blocks)
        if self.on_context_blocks_change:
            self.on_context_blocks_change(list(self._context_blocks))
