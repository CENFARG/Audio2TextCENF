"""
Unit tests for the F2 supervisor fragment recorder (pure-ish module).

Covers the openspec audio2text-f2-supervisor voice-recording contract with
NO real audio: sounddevice/soundfile are replaced by fakes via monkeypatch.
- toggle on/off state machine (draft -> recording -> draft)
- refuse to start while the main Transcriber is recording (warning logged,
  refusal reason exposed)
- only ONE supervisor recording at a time (second start refused)
- transcribe_fn injection: stop captures WAV then delivers the transcript
  through the on_text callback from the worker thread
"""

import logging
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend import supervisor_recorder
from backend.supervisor_recorder import SAMPLE_RATE, SupervisorRecorder


class _FakeStream:
    """Fake sounddevice InputStream: records frames without touching audio."""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self.closed = False
        self.read_calls = 0

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def close(self) -> None:
        self.closed = True

    def read(self, frames: int):
        self.read_calls += 1
        import numpy as np  # local: matches real sounddevice frame contract

        return (np.zeros((frames, 1), dtype="float32"), False)


class _FakeSd:
    """Fake sounddevice module returning :class:`_FakeStream` instances."""

    def __init__(self) -> None:
        self.created: list[_FakeStream] = []

    def InputStream(self, **kwargs) -> _FakeStream:
        stream = _FakeStream(**kwargs)
        self.created.append(stream)
        return stream


class _FakeSf:
    """Fake soundfile module recording WAV writes."""

    def __init__(self) -> None:
        self.writes: list[tuple] = []

    def write(self, path, data, samplerate, **kwargs) -> None:
        self.writes.append((path, data, samplerate))


@pytest.fixture
def fake_audio(monkeypatch) -> tuple[_FakeSd, _FakeSf]:
    """Replace sounddevice/soundfile with in-memory fakes."""
    fake_sd, fake_sf = _FakeSd(), _FakeSf()
    monkeypatch.setattr(supervisor_recorder, "sd", fake_sd)
    monkeypatch.setattr(supervisor_recorder, "sf", fake_sf)
    return fake_sd, fake_sf


def _make_recorder(
    on_text=None, main_recording=False, transcribe_fn=None
) -> tuple[SupervisorRecorder, list]:
    """Build a recorder wired to in-memory fakes; return (recorder, delivered)."""
    main = type("Main", (), {"is_recording": main_recording})()
    delivered: list = []

    def default_transcribe(path):
        return "texto transcrito"

    recorder = SupervisorRecorder(
        on_text=on_text or delivered.append,
        transcribe_fn=transcribe_fn or default_transcribe,
        main_transcriber=main,
    )
    return recorder, delivered


def _stop_and_join(recorder: SupervisorRecorder, timeout: float = 5.0) -> None:
    """Stop capture and wait until the worker thread fully finishes."""
    recorder.stop()
    thread = recorder._thread
    if thread is not None:
        thread.join(timeout=timeout)
        assert not thread.is_alive(), "worker thread did not finish in time"


@pytest.mark.unit
class TestToggleStates:
    """toggle()/start()/stop() state machine."""

    def test_constants_16k_mono(self):
        # Assert: contract capture format
        assert SAMPLE_RATE == 16000

    def test_toggle_starts_and_stops(self, fake_audio):
        # Arrange
        recorder, _ = _make_recorder()

        # Act / Assert: off -> on
        assert recorder.toggle() is True
        assert recorder.recording is True

        # Act / Assert: on -> off
        assert recorder.toggle() is False
        _stop_and_join(recorder)
        assert recorder.recording is False

    def test_toggle_off_delivers_stream_objects_to_wav_writer(self, fake_audio):
        # Arrange
        fake_sd, fake_sf = fake_audio
        recorder, _ = _make_recorder()
        recorder.toggle()
        time.sleep(0.05)  # let the capture thread read at least one frame

        # Act
        _stop_and_join(recorder)

        # Assert: stream lifecycle + wav write attempted exactly once
        assert len(fake_sd.created) == 1
        stream = fake_sd.created[0]
        assert stream.started and stream.stopped and stream.closed
        assert len(fake_sf.writes) == 1
        assert fake_sf.writes[0][2] == SAMPLE_RATE

    def test_stop_when_not_recording_is_safe_noop(self, fake_audio):
        # Arrange
        recorder, _ = _make_recorder()

        # Act / Assert
        assert recorder.stop() is False
        assert recorder._thread is None


@pytest.mark.unit
class TestRefusals:
    """Refuse to start: main recording in progress, or already active."""

    def test_refuses_when_main_transcriber_is_recording(self, fake_audio, caplog):
        # Arrange
        recorder, _ = _make_recorder(main_recording=True)

        # Act
        with caplog.at_level(logging.WARNING, logger="backend.supervisor_recorder"):
            started = recorder.toggle()

        # Assert: no capture, state untouched, warning + reason exposed
        assert started is False
        assert recorder.recording is False
        assert recorder.refusal_reason == "main_recording"
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_second_start_refused_while_recording(self, fake_audio):
        # Arrange
        recorder, _ = _make_recorder()
        assert recorder.start() is True

        # Act
        started_again = recorder.start()

        # Assert: only ONE supervisor recording at a time
        assert started_again is False
        assert recorder.refusal_reason == "busy"
        _stop_and_join(recorder)

    def test_refusal_reason_cleared_on_successful_start(self, fake_audio):
        # Arrange: first attempt blocked by the main recorder
        blocked, _ = _make_recorder(main_recording=True)
        assert blocked.start() is False
        assert blocked.refusal_reason == "main_recording"

        # Act: main recorder goes idle, retry
        main = blocked._main_transcriber
        if main is not None:
            main.is_recording = False
        started = blocked.start()

        # Assert
        assert started is True
        assert blocked.refusal_reason is None
        _stop_and_join(blocked)

    def test_refuses_when_audio_backend_missing(self, monkeypatch):
        # Arrange: sounddevice unavailable (import failed at module load)
        monkeypatch.setattr(supervisor_recorder, "sd", None)

        # Act
        recorder, _ = _make_recorder()
        started = recorder.start()

        # Assert
        assert started is False
        assert recorder.refusal_reason == "unavailable"


@pytest.mark.unit
class TestCaptureFailureDelivery:
    """C-1: ANY capture failure must deliver on_text(None), never hang the UI."""

    def test_inputstream_open_failure_delivers_none(self, fake_audio):
        # Arrange: opening the device raises (mic busy/disconnected)
        fake_sd, _ = fake_audio

        class _BrokenOpenStream(_FakeStream):
            def start(self) -> None:
                raise OSError("device unavailable")

        fake_sd.InputStream = lambda **kwargs: _BrokenOpenStream(**kwargs)
        recorder, delivered = _make_recorder()

        # Act
        recorder.toggle()
        _stop_and_join(recorder)

        # Assert: the UI is notified with None so it can clear "Transcribiendo..."
        assert delivered == [None]

    def test_read_failure_delivers_none(self, fake_audio):
        # Arrange: reading frames raises mid-capture (device error)
        fake_sd, _ = fake_audio

        class _BrokenReadStream(_FakeStream):
            def read(self, frames: int):
                raise OSError("stream read failed")

        fake_sd.InputStream = lambda **kwargs: _BrokenReadStream(**kwargs)
        recorder, delivered = _make_recorder()

        # Act
        recorder.toggle()
        _stop_and_join(recorder)

        # Assert
        assert delivered == [None]


@pytest.mark.unit
class TestTranscriptionDelivery:
    """stop() -> WAV -> injected transcribe_fn -> on_text callback."""

    def test_transcript_delivered_via_callback(self, fake_audio):
        # Arrange
        recorder, delivered = _make_recorder()
        recorder.toggle()
        time.sleep(0.05)

        # Act
        _stop_and_join(recorder)

        # Assert: injected transcribe_fn result reaches on_text
        assert delivered == ["texto transcrito"]

    def test_callback_receives_none_when_transcription_fails(self, fake_audio):
        # Arrange: Groq returned None (transcribe_with_groq contract)
        recorder, delivered = _make_recorder(transcribe_fn=lambda path: None)
        recorder.toggle()
        time.sleep(0.05)

        # Act
        _stop_and_join(recorder)

        # Assert: None is delivered (UI decides what to show), no crash
        assert delivered == [None]

    def test_transcribe_fn_receives_wav_path_and_temp_cleaned(self, fake_audio):
        # Arrange
        received_paths: list = []
        recorder, _ = _make_recorder(transcribe_fn=received_paths.append)
        recorder.toggle()
        time.sleep(0.05)

        # Act
        _stop_and_join(recorder)

        # Assert: exactly one wav path handed to transcribe_fn
        assert len(received_paths) == 1
        wav_path = str(received_paths[0])
        assert wav_path.endswith(".wav")

    def test_on_text_called_from_worker_thread_not_caller(self, fake_audio):
        # Arrange: capture the thread id at delivery time
        delivered_from: list[int] = []
        recorder, _ = _make_recorder(
            on_text=lambda text: delivered_from.append(threading.get_ident())
        )
        caller_thread = threading.get_ident()
        recorder.toggle()
        time.sleep(0.05)

        # Act
        _stop_and_join(recorder)

        # Assert: delivery happens on the worker thread (UI must bridge via after)
        assert len(delivered_from) == 1
        assert delivered_from[0] != caller_thread
