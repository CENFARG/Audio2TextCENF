"""@File: audio2text/services/audio_capture_service.py
@Description: AudioCaptureService — thread-safe audio recording with sounddevice.
    Manages recording lifecycle: start, stop, buffer, duration tracking, priority app detection.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto

import numpy as np
import psutil  # type: ignore[import-untyped]
import soundfile as sf  # type: ignore[import-untyped]

from audio2text.domain.audio import AudioSegment
from audio2text.services._recorder import Recorder


class CaptureState(Enum):
    """Recording state machine states."""

    IDLE = auto()
    RECORDING = auto()
    PROCESSING = auto()


@dataclass
class AudioCaptureConfig:
    """Configuration for audio capture.

    Attributes:
        sample_rate: Audio sample rate in Hz (default 16000).
        channels: Number of audio channels (default 1 = mono).
        max_recording_time: Maximum recording time in seconds (default 300).
        buffer_size: Number of frames per read from the audio stream.
        priority_apps: App names that block recording if running.
    """

    sample_rate: int = 16000
    channels: int = 1
    max_recording_time: float = 300.0
    buffer_size: int = 1024
    priority_apps: list[str] = field(
        default_factory=lambda: ["zoom", "teams", "meet", "skype", "discord"]
    )


class AudioCaptureService:
    """Thread-safe audio capture service using sounddevice.

    Manages the full recording lifecycle:
    - Checks for priority applications before starting.
    - Delegates stream ops to Recorder (extracted to _recorder.py).
    - Handles state transitions and callback emissions.
    - Saves captured audio to a temporary WAV file on stop.

    Thread safety is ensured via ``threading.Lock`` on all state-changing operations.
    """

    def __init__(
        self,
        config: AudioCaptureConfig,
        status_callback: Callable[[str, str], None],
        overlay_callback: Callable[[str, int, int], None],
    ) -> None:
        """Initialize the audio capture service.

        Args:
            config: Capture configuration (sample rate, max time, etc.).
            status_callback: Called with (text, color) on status changes.
            overlay_callback: Called with (state, minutes, seconds) for overlay updates.
        """
        self._config = config
        self._status_callback = status_callback
        self._overlay_callback = overlay_callback

        self._lock = threading.Lock()
        self._is_recording = False
        self._state = CaptureState.IDLE
        self._recording_start_time: float = 0.0
        self._recorder: Recorder | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_recording(self) -> bool:
        """Start audio recording.

        Checks for priority applications first. If any are found, recording
        is rejected and the status callback is invoked with a warning.

        Returns:
            True if recording started successfully, False otherwise.
        """
        with self._lock:
            if self._is_recording:
                return False

            # Check for priority apps
            if self._check_priority_apps():
                self._status_callback("priority_app_in_use", "orange")
                return False

            self._is_recording = True
            self._state = CaptureState.RECORDING
            self._recording_start_time = time.time()

        self._emit_start()

        self._recorder = Recorder(
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
            buffer_size=self._config.buffer_size,
            max_recording_time=self._config.max_recording_time,
            status_callback=self._status_callback,
            overlay_callback=self._overlay_callback,
            on_auto_stop=self._on_recorder_auto_stop,
        )

        if not self._recorder.start():
            with self._lock:
                self._is_recording = False
                self._state = CaptureState.IDLE
            return False

        return True

    def stop_recording(self) -> AudioSegment | None:
        """Stop audio recording and return the captured audio.

        Returns:
            An AudioSegment if audio was captured, or None if no data was recorded.
        """
        with self._lock:
            if self._state == CaptureState.IDLE:
                return None

            self._is_recording = False
            self._state = CaptureState.PROCESSING

        self._emit_processing()

        if self._recorder:
            self._recorder.stop()
            self._recorder.join(timeout=2.0)
            audio_data = self._recorder.get_audio_data()
            self._recorder = None
        else:
            audio_data = []

        audio_segment = self._build_audio_segment(audio_data)

        with self._lock:
            self._state = CaptureState.IDLE

        return audio_segment

    def is_recording(self) -> bool:
        """Check if recording is currently active."""
        return self._is_recording

    def get_duration(self) -> float:
        """Get the elapsed recording duration in seconds."""
        if not self._is_recording:
            return 0.0
        return time.time() - self._recording_start_time

    @property
    def state(self) -> CaptureState:
        """Current state of the capture service."""
        return self._state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_priority_apps(self) -> bool:
        """Check if any priority applications are running."""
        priority_set = {app.lower() for app in self._config.priority_apps}
        try:
            for proc in psutil.process_iter(["name"]):
                name = (proc.info["name"] or "").lower()
                for app in priority_set:
                    if app in name:
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return False

    def _on_recorder_auto_stop(self) -> None:
        """Handle automatic stop triggered by recorder (e.g. max time)."""
        self._is_recording = False
        self._state = CaptureState.PROCESSING
        self._emit_processing()

    def _emit_start(self) -> None:
        """Emit callbacks for recording start."""
        self._status_callback("status_recording", "green")
        self._overlay_callback("recording", 0, 0)

    def _emit_processing(self) -> None:
        """Emit callbacks for processing state."""
        self._status_callback("status_processing", "yellow")
        self._overlay_callback("processing", 0, 0)

    def _build_audio_segment(
        self, audio_data: list
    ) -> AudioSegment | None:
        """Combine audio data chunks and return an AudioSegment.

        Writes the combined audio to a temporary WAV file and creates
        an AudioSegment with the in-memory numpy data.
        """
        if not audio_data:
            return None

        full_audio = np.concatenate(audio_data, axis=0)

        if full_audio.size == 0:
            return None

        # Write to temporary WAV file
        try:
            import os

            fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="a2t_")
            os.close(fd)
            sf.write(temp_path, full_audio, self._config.sample_rate)
        except Exception:
            return None

        return AudioSegment(
            data=full_audio,
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
        )
