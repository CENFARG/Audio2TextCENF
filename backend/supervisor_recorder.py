"""
Supervisor fragment recorder for the F2 Supervisor tab (pure-ish module).

Captures 16 kHz mono microphone audio to a temp WAV via sounddevice on a
background thread; on stop, writes the WAV, runs the INJECTED ``transcribe_fn``
(by default ``Transcriber.transcribe_with_groq``) on the same worker thread
and delivers the transcript (str, or None on failure) through the ``on_text``
callback. The UI owns thread-bridging (deliver via ``Tk.after``).

Refusals (never raise): main Transcriber already recording, a supervisor
recording already active ("busy"), or an unavailable audio backend. The
refusal reason is exposed via ``refusal_reason`` (``None`` after a
successful start) so the UI can show the right status message.
"""

from __future__ import annotations

import logging
import os
import tempfile
import threading
import time

import numpy as np

logger = logging.getLogger(__name__)

try:  # audio backend may be missing in stripped environments
    import sounddevice as sd
except Exception:  # pragma: no cover - exercised via monkeypatched None
    sd = None  # type: ignore[assignment]

try:
    import soundfile as sf
except Exception:  # pragma: no cover - soundfile is a hard dependency
    sf = None  # type: ignore[assignment]

#: Capture format contract: 16 kHz mono (spec: F2 voice recording).
SAMPLE_RATE = 16000

#: Seconds between capture polls (bounded busy-wait on the worker thread).
_POLL_SECONDS = 0.05

#: Refusal reason: the main Transcriber is capturing right now.
REFUSAL_MAIN_RECORDING = "main_recording"

#: Refusal reason: a supervisor recording is already active.
REFUSAL_BUSY = "busy"

#: Refusal reason: sounddevice/soundfile backend unavailable.
REFUSAL_UNAVAILABLE = "unavailable"


class SupervisorRecorder:
    """Single fragment recorder: one capture at a time, transcribe on stop.

    Args:
        on_text: Callback invoked with the transcript (``str | None``) from
            the worker thread once transcription finishes.
        transcribe_fn: Injected ``path -> str | None`` transcription
            function (``Transcriber.transcribe_with_groq`` in the app).
        main_transcriber: Main app Transcriber instance; its ``is_recording``
            flag blocks supervisor recording to avoid device contention.
    """

    def __init__(self, on_text, transcribe_fn, main_transcriber=None) -> None:
        self._on_text = on_text
        self._transcribe_fn = transcribe_fn
        self._main_transcriber = main_transcriber
        self._recording = False
        self._refusal_reason: str | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # ── State ────────────────────────────────────────────────────────
    @property
    def recording(self) -> bool:
        """Whether a supervisor capture is currently running."""
        return self._recording

    @property
    def refusal_reason(self) -> str | None:
        """Reason of the last refused start, or ``None`` after success."""
        return self._refusal_reason

    # ── Control ──────────────────────────────────────────────────────
    def toggle(self) -> bool:
        """Toggle recording: start when idle, stop when capturing.

        Returns:
            ``True`` when a recording was started, ``False`` otherwise
            (stopped, or the start was refused — see ``refusal_reason``).
        """
        if self._recording:
            self.stop()
            return False
        return self.start()

    def start(self) -> bool:
        """Start a 16 kHz mono capture on a background thread.

        Returns:
            ``True`` when the capture started; ``False`` when refused
            (main recording active, already capturing, or backend missing).
        """
        with self._lock:
            if self._recording:
                self._refusal_reason = REFUSAL_BUSY
                logger.warning("Supervisor recording already active; start refused")
                return False
            if getattr(self._main_transcriber, "is_recording", False):
                self._refusal_reason = REFUSAL_MAIN_RECORDING
                logger.warning("Supervisor recording refused: main Transcriber is recording")
                return False
            if sd is None or sf is None:
                self._refusal_reason = REFUSAL_UNAVAILABLE
                logger.warning("Supervisor recording refused: audio backend missing")
                return False
            self._refusal_reason = None
            self._stop_event = threading.Event()
            self._thread = threading.Thread(
                target=self._capture_loop, name="supervisor-recorder", daemon=True
            )
            self._recording = True
            self._thread.start()
            return True

    def stop(self) -> bool:
        """Signal the capture thread to finalize, transcribe and deliver.

        Returns:
            ``True`` when a running capture was signaled, ``False`` when
            idle (safe no-op).
        """
        if not self._recording:
            return False
        self._stop_event.set()
        self._recording = False
        return True

    # ── Worker ───────────────────────────────────────────────────────
    def _capture_loop(self) -> None:
        """Capture frames until stop, then write WAV and deliver transcript.

        Runs entirely on the worker thread: reads the InputStream in bounded
        polls, finalizes the stream, writes a temp WAV, calls the injected
        ``transcribe_fn`` and forwards the result to ``on_text``. The temp
        WAV is removed afterwards. EVERY failure path (backend missing,
        stream raise, zero frames, transcription error) delivers
        ``on_text(None)`` so the UI can never stay stuck on
        "Transcribiendo..." (C-1); failures are logged, never raised.
        """
        stream = None
        wav_path: str | None = None
        frames: list = []
        if sd is None or sf is None:
            logger.error("Supervisor capture failed: audio backend missing")
            self._on_text(None)
            return
        try:
            stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            stream.start()
            while not self._stop_event.is_set():
                data, overflowed = stream.read(int(SAMPLE_RATE * _POLL_SECONDS))
                frames.append(data)
                if overflowed:  # pragma: no cover - device-level condition
                    logger.warning("Supervisor recording overflowed audio buffer")
                time.sleep(0.005)
        except Exception as exc:
            logger.error("Supervisor capture failed: %s", exc)
        finally:
            try:
                if stream is not None:
                    stream.stop()
                    stream.close()
            except Exception as exc:  # pragma: no cover - device cleanup
                logger.warning("Supervisor stream cleanup failed: %s", exc)

        if not frames:
            # C-1: notify the UI even when nothing was captured, so it clears
            # the "Transcribiendo..." state and shows a localized error.
            logger.warning("Supervisor recording produced no audio; nothing to transcribe")
            self._on_text(None)
            return
        try:
            wav_path = self._write_wav(frames)
            transcript = self._transcribe_fn(wav_path)
            self._on_text(transcript)
        except Exception as exc:
            logger.error("Supervisor transcription failed: %s", exc)
            self._on_text(None)
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:  # pragma: no cover - temp cleanup best effort
                    logger.debug("Supervisor temp wav already removed: %s", wav_path)

    def _write_wav(self, frames: list) -> str:
        """Persist captured frames to a temp 16 kHz mono WAV file.

        Args:
            frames: Captured audio blocks from the InputStream.

        Returns:
            Path of the written temp WAV file (caller unlinks it).

        Raises:
            Exception: Propagates soundfile write failures to the worker.
        """
        fd, wav_path = tempfile.mkstemp(suffix=".wav", prefix="supervisor_")
        os.close(fd)
        if sf is None:  # narrowed by callers; explicit for safety
            raise RuntimeError("soundfile backend unavailable")
        audio = np.concatenate(frames, axis=0)
        sf.write(wav_path, audio, SAMPLE_RATE)
        return wav_path
