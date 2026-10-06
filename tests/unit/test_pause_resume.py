"""
Unit tests for REQ-1 pause/resume recording (state machine ARCH-009).

Contract under test (public interface of ``backend.transcriber.Transcriber``):
- state machine: recording -> paused -> recording -> stopped
- ``pause_recording``: only while recording (not already paused); closes the
  InputStream WITHOUT flushing/processing; keeps ``audio_data``; timer stops.
- ``resume_recording``: only while paused; reopens the stream; appends
  continue onto the kept buffer (no flush, no reset).
- while paused: audio capture suspended, streaming snapshots suspended.
- stop after resume yields ONE combined recording (pre-pause + post-resume
  audio in the single snapshot handed to ``process_recording``).
- pause elapsed time is subtracted from wall time so the recording timer
  freezes while paused and the max-recording-time budget is not consumed.

All audio interaction runs through a fake ``sd.InputStream`` patched at
``backend.transcriber.sd.InputStream`` — no microphone, no Groq, no files.
"""

import json
import sys
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

LANG_DIR = Path(__file__).resolve().parents[2] / "lang"
EXAMPLE_CONFIG = Path(__file__).resolve().parents[2] / "config.json.example"


class _FakeInputStream:
    """Deterministic sd.InputStream double: each read returns a new amplitude.

    ``instance_log`` records every constructed instance so tests can assert
    the stream was closed on pause and RE-opened (new instance) on resume.
    """

    instance_log: list["_FakeInputStream"] = []

    def __init__(self, samplerate=16000, channels=1, dtype="float32", **_kw):
        self.samplerate = samplerate
        self.active = True
        self.stop_calls = 0
        self.close_calls = 0
        self._amplitude = 0.01 * (len(_FakeInputStream.instance_log) + 1)
        _FakeInputStream.instance_log.append(self)

    def start(self):
        self.active = True

    def stop(self):
        self.stop_calls += 1
        self.active = False

    def close(self):
        self.close_calls += 1
        self.active = False

    def read(self, frames):
        time.sleep(0.002)  # pace the hot loop like a real capture device
        chunk = np.full((frames, 1), self._amplitude, dtype="float32")
        return chunk, False


def _make_config():
    cm = Mock()
    cm.get.side_effect = lambda k, d=None: {
        "hotkey": "f9",
        "record_mode": "toggle",
        "audio_priority_apps": [],
        "utf8_validation": True,
        "blocks": {},
        "max_recording_time": 720,
        "transcription_language": "es",
        "default_language": "es",
        "save_audio": False,
    }.get(k, d)
    cm.get_groq_api_key_from_env = Mock(return_value="gsk_test_dummy")
    return cm


def _make_transcriber():
    """Build a real Transcriber against fakes (no mic, no API, no files).

    Patches for Groq/NvidiaASR/sd.InputStream are applied by the autouse
    ``_fake_audio_stack`` fixture so they stay active for the whole test.
    """
    from backend.transcriber import Transcriber

    cm = _make_config()
    fm = Mock()
    tr = Transcriber(cm, Mock(), fm, Mock(), Mock(), Mock())
    # Snapshot capture: intercept the post-stop handoff instead of running
    # the real process_recording (which would call Groq / write files).
    tr.process_recording = Mock()
    return tr


def _wait_until(predicate, timeout_s=2.0, step_s=0.02):
    """Poll ``predicate`` until true or timeout; returns the last value."""
    deadline = time.time() + timeout_s
    value = predicate()
    while not value and time.time() < deadline:
        time.sleep(step_s)
        value = predicate()
    return value


@pytest.fixture(autouse=True)
def _fake_audio_stack():
    """Patch Groq/Nvidia/sounddevice for the WHOLE test (helper cannot: its
    ``with`` would exit before the test body runs, leaving the REAL mic open)."""
    _FakeInputStream.instance_log = []
    with patch("backend.transcriber.Groq", return_value=Mock()), patch(
        "backend.transcriber.NvidiaASR"
    ), patch("backend.transcriber.sd.InputStream", _FakeInputStream):
        yield
    _FakeInputStream.instance_log = []


@pytest.mark.unit
class TestPauseResumeStateMachine:
    """recording -> paused -> recording -> stopped (ARCH-009)."""

    def test_pause_closes_stream_and_keeps_buffer(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0), "capture never produced audio"

        # Act
        assert tr.pause_recording() is True

        # The loop may land one in-flight chunk after the pause transition;
        # give it a beat, then the buffer must be FROZEN from here on.
        time.sleep(0.1)
        frozen = len(tr.audio_data)

        # Assert: paused, stream closed WITHOUT processing, buffer KEPT.
        assert tr.is_paused is True
        assert tr.is_recording is True  # still one session
        assert tr.input_stream is None
        assert frozen > 0
        closed = _FakeInputStream.instance_log[0]
        assert closed.close_calls == 1
        assert closed.stop_calls == 1
        time.sleep(0.25)
        assert len(tr.audio_data) == frozen, "capture continued after pause"
        tr.stop_recording()

    def test_capture_suspended_while_paused(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        assert tr.pause_recording() is True
        time.sleep(0.1)  # let any in-flight chunk land
        frozen = len(tr.audio_data)

        # Act: give the (alive) record loop time; paused means NO reads.
        time.sleep(0.3)

        # Assert
        assert len(tr.audio_data) == frozen
        tr.stop_recording()

    def test_resume_reopens_stream_and_continues_appending(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        tr.pause_recording()
        frozen = len(tr.audio_data)

        # Act
        assert tr.resume_recording() is True

        # Assert: a NEW stream instance was opened and capture resumes.
        assert tr.is_paused is False
        assert tr.is_recording is True
        assert tr.input_stream is not None
        assert tr.input_stream is not _FakeInputStream.instance_log[0]
        assert _wait_until(lambda: len(tr.audio_data) > frozen), "no capture after resume"
        tr.stop_recording()

    def test_stop_after_resume_produces_one_combined_recording(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        pre_pause = len(tr.audio_data)
        tr.pause_recording()
        frozen = len(tr.audio_data)
        tr.resume_recording()
        assert _wait_until(lambda: len(tr.audio_data) > frozen + 3)

        # Act
        tr.stop_recording()
        assert _wait_until(lambda: tr.process_recording.call_count == 1)

        # Assert: ONE combined snapshot = full buffer (pre-pause + post-resume).
        args, _ = tr.process_recording.call_args
        combined_snapshot = args[1]  # (recording_id, audio_snapshot, ...)
        assert len(combined_snapshot) == len(tr.audio_data)
        assert len(combined_snapshot) > pre_pause
        # Chunks are ordered: first stream amplitude < resumed stream amplitude.
        assert combined_snapshot[0][0][0] < combined_snapshot[-1][0][0]
        assert tr.is_paused is False
        assert tr.is_recording is False

    def test_pause_twice_is_ignored(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        assert tr.pause_recording() is True

        # Act / Assert: already paused — guard rejects, state unchanged.
        assert tr.pause_recording() is False
        assert tr.is_paused is True
        tr.stop_recording()

    def test_pause_ignored_when_not_recording(self):
        tr = _make_transcriber()

        # Act / Assert
        assert tr.pause_recording() is False
        assert tr.is_paused is False
        assert tr.is_recording is False

    def test_resume_ignored_when_not_paused(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        assert tr.is_paused is False

        # Act / Assert: recording but NOT paused — resume is illegal.
        assert tr.resume_recording() is False
        assert tr.is_paused is False
        tr.stop_recording()

        # ...and once stopped, resume stays illegal.
        assert tr.resume_recording() is False

    def test_stop_clears_paused_state(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        tr.pause_recording()

        # Act
        tr.stop_recording()

        # Assert: stopped is terminal — no lingering paused flag.
        assert _wait_until(lambda: tr.process_recording.call_count == 1)
        assert tr.is_paused is False
        assert tr.is_recording is False


@pytest.mark.unit
class TestPauseTimerOffset:
    """Paused time is subtracted from wall time: timer freezes, budget safe."""

    def test_in_flight_pause_counts_into_offset(self):
        tr = _make_transcriber()
        tr.is_paused = True
        tr._pause_started = 1000.0

        # Act / Assert: 5s into the pause -> 5s of offset.
        assert tr._pause_elapsed_seconds(now=1005.0) == pytest.approx(5.0)

    def test_completed_pause_folds_into_accumulated_total(self):
        tr = _make_transcriber()
        tr._pause_total = 0.0
        tr._pause_started = 1000.0
        tr.is_paused = True

        # Act: simulate the resume fold with a fixed clock.
        tr._pause_total += 1005.0 - tr._pause_started
        tr._pause_started = None
        tr.is_paused = False

        # Assert
        assert tr._pause_total == pytest.approx(5.0)
        assert tr._pause_elapsed_seconds(now=1010.0) == pytest.approx(5.0)

    def test_no_pause_means_zero_offset(self):
        tr = _make_transcriber()
        assert tr._pause_elapsed_seconds(now=1234.0) == 0.0

    def test_timer_events_stop_while_paused(self):
        tr = _make_transcriber()

        def _drain_queue():
            events = []
            while True:
                event = tr.get_timer_event()
                if event is None:
                    return events
                events.append(event)

        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        assert tr.pause_recording() is True
        # Let any pre-pause in-flight push land, then DISCARD everything:
        # only events produced while paused are asserted below.
        time.sleep(0.05)
        _drain_queue()

        # Act: give the paused loop time to (wrongly) tick.
        time.sleep(0.35)
        drained = _drain_queue()

        # Assert: no timer ticks and no streaming while paused.
        assert all(event[0] not in ("timer", "streaming") for event in drained)
        tr.stop_recording()

    def test_streaming_snapshots_suspended_while_paused(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        # Make the streaming snapshot immediately due, then pause.
        tr._stream_next_trigger = time.time()
        assert tr.pause_recording() is True
        tr._stream_snapshot_and_submit = Mock()

        # Act
        time.sleep(0.35)

        # Assert: paused loop must NOT snapshot/stream.
        assert tr._stream_snapshot_and_submit.call_count == 0
        tr.stop_recording()


@pytest.mark.unit
class TestPauseHotkeyConfig:
    """``pause_hotkey`` config key: default ctrl+alt+p, shipped in the example."""

    def test_default_config_has_pause_hotkey(self):
        # Arrange: real defaults without touching the user's config.json
        from backend.config_manager import ConfigManager

        defaults = ConfigManager(config_file=str(EXAMPLE_CONFIG.parent / "no-such-config.json"))

        # Act / Assert
        assert defaults.default_config.get("pause_hotkey") == "ctrl+alt+p"

    @pytest.mark.parametrize("lang", ["es", "en"])
    def test_status_message_keys_exist_in_both_langs(self, lang):
        translations = json.loads((LANG_DIR / f"{lang}.json").read_text(encoding="utf-8"))

        # Act / Assert
        assert "recording_paused" in translations
        assert "recording_resumed" in translations
        assert translations["recording_paused"].strip() != ""
        assert translations["recording_resumed"].strip() != ""

    def test_example_config_documents_pause_hotkey(self):
        example = json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))

        # Act / Assert
        assert example.get("pause_hotkey") == "ctrl+alt+p"


@pytest.mark.unit
class TestPauseThreadSafety:
    """pause/resume are callable from the keyboard-listener thread."""

    def test_pause_resume_survive_parallel_calls(self):
        tr = _make_transcriber()
        tr.start_recording()
        assert _wait_until(lambda: len(tr.audio_data) > 0)
        errors: list[Exception] = []

        def hammer():
            for _ in range(20):
                try:
                    tr.pause_recording()
                    tr.resume_recording()
                except Exception as exc:  # pragma: no cover - failure path
                    errors.append(exc)

        threads = [threading.Thread(target=hammer, daemon=True) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5.0)

        # Assert: no exception escaped; the machine ends in a coherent state.
        assert errors == []
        assert tr.is_recording is True
        assert tr.is_paused is False
        tr.stop_recording()
