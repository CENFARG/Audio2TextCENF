"""@File: audio2text/services/_recorder.py
@Description: Low-level sounddevice recording loop and stream management.
    Extracted from AudioCaptureService to keep module under 250 lines.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

import numpy as np
import numpy.typing as npt
import sounddevice as sd  # type: ignore[import-untyped]


class Recorder:
    """Manages the sounddevice InputStream and background recording thread.

    Handles buffer overflow detection, max recording time enforcement,
    and automatic stop triggering.
    """

    def __init__(
        self,
        sample_rate: int,
        channels: int,
        buffer_size: int,
        max_recording_time: float,
        status_callback: Callable[[str, str], None],
        overlay_callback: Callable[[str, int, int], None],
        on_auto_stop: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the recorder.

        Args:
            sample_rate: Audio sample rate in Hz.
            channels: Number of audio channels.
            buffer_size: Frames per read from the audio stream.
            max_recording_time: Maximum recording time in seconds.
            status_callback: Called with (text, color) on status changes.
            overlay_callback: Called with (state, minutes, seconds) for overlay.
        """
        self._sample_rate = sample_rate
        self._channels = channels
        self._buffer_size = buffer_size
        self._max_time = max_recording_time
        self._status_callback = status_callback
        self._overlay_callback = overlay_callback
        self._on_auto_stop = on_auto_stop

        self._stop_event = threading.Event()
        self._input_stream: sd.InputStream | None = None  # type: ignore[valid-type]
        self._thread: threading.Thread | None = None
        self._audio_data: list[npt.NDArray[np.float32]] = []

    # ------------------------------------------------------------------
    # Stream lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Create and start the InputStream and background recording thread.

        Returns:
            True if the stream started successfully.
        """
        try:
            self._stop_event.clear()
            self._audio_data.clear()

            self._input_stream = sd.InputStream(
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="float32",
            )
            self._input_stream.start()

            self._thread = threading.Thread(
                target=self._record_loop, daemon=True
            )
            self._thread.start()
            return True
        except Exception:
            self._status_callback("audio_error_mic_in_use", "red")
            return False

    def stop(self) -> None:
        """Signal the recording loop to stop and close the stream.

        Does NOT join the thread — caller must call `join()` after.
        """
        self._stop_event.set()
        self._close_stream()

    def join(self, timeout: float = 2.0) -> None:
        """Wait for the recording thread to finish.

        Args:
            timeout: Maximum seconds to wait.
        """
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def get_audio_data(self) -> list[npt.NDArray[np.float32]]:
        """Return the captured audio data chunks."""
        return list(self._audio_data)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _close_stream(self) -> None:
        """Stop and close the InputStream if active."""
        if self._input_stream:
            try:
                self._input_stream.stop()
                self._input_stream.close()
            except Exception:
                pass
            self._input_stream = None

    def _record_loop(self) -> None:
        """Background thread that reads audio data from the stream.

        Reads chunks of audio data, appends them to a buffer, handles
        overflow warnings, updates duration, and emits overlay callbacks.
        Stops when the stop event is set or max recording time is reached.
        """
        start_time = time.time()

        while not self._stop_event.is_set():
            try:
                if self._input_stream and self._input_stream.active:
                    data, overflowed = self._input_stream.read(self._buffer_size)
                    if overflowed:
                        self._status_callback("buffer_overflow", "yellow")
                    self._audio_data.append(data)

                elapsed = time.time() - start_time
                if elapsed > self._max_time:
                    self._trigger_auto_stop()
                    break

                minutes, seconds = divmod(int(elapsed), 60)
                self._status_callback(
                    f"status_recording {minutes:02d}:{seconds:02d}", "green"
                )
                self._overlay_callback("recording", minutes, seconds)

            except Exception:
                self._trigger_auto_stop()
                break

    def _trigger_auto_stop(self) -> None:
        """Trigger an automatic stop from within the recording thread."""
        self._stop_event.set()
        if self._on_auto_stop:
            self._on_auto_stop()
