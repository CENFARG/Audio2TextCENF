"""@File: tests/unit/test_audio_capture_service.py
@Description: Unit tests for AudioCaptureService (Task 3.1). TDD cycle — RED first.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np

# ============================================================================
# RED phase — these imports will fail until AudioCaptureService is implemented.
# ============================================================================


class TestAudioCaptureServiceInit:
    """Tests for AudioCaptureService initialization and configuration."""

    def test_initial_state_is_idle(self) -> None:
        """A newly created service starts in IDLE state."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
            CaptureState,
        )

        status_calls: list[tuple[str, str]] = []
        overlay_calls: list[tuple[str, int, int]] = []

        def on_status(text: str, color: str) -> None:
            status_calls.append((text, color))

        def on_overlay(state: str, minutes: int, seconds: int) -> None:
            overlay_calls.append((state, minutes, seconds))

        config = AudioCaptureConfig()
        service = AudioCaptureService(
            config=config,
            status_callback=on_status,
            overlay_callback=on_overlay,
        )
        assert service.state == CaptureState.IDLE
        assert service.is_recording() is False
        assert service.get_duration() == 0.0

    def test_default_config_values(self) -> None:
        """AudioCaptureConfig has sensible defaults."""
        from audio2text.services.audio_capture_service import AudioCaptureConfig

        config = AudioCaptureConfig()
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.max_recording_time == 300.0
        assert config.buffer_size == 1024
        assert "zoom" in config.priority_apps

    def test_custom_config_values(self) -> None:
        """AudioCaptureConfig accepts custom values."""
        from audio2text.services.audio_capture_service import AudioCaptureConfig

        config = AudioCaptureConfig(
            sample_rate=44100,
            channels=2,
            max_recording_time=60.0,
            buffer_size=2048,
            priority_apps=["msteams", "webex"],
        )
        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.max_recording_time == 60.0
        assert config.buffer_size == 2048
        assert "msteams" in config.priority_apps


class TestAudioCaptureServiceRecording:
    """Tests for recording lifecycle (start/stop with mocked hardware)."""

    def test_start_recording_returns_true_when_no_priority_apps(self) -> None:
        """start_recording succeeds when no priority apps are running."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        status_calls: list[tuple[str, str]] = []

        def on_status(text: str, color: str) -> None:
            status_calls.append((text, color))

        config = AudioCaptureConfig(priority_apps=["zoom"])
        service = AudioCaptureService(
            config=config,
            status_callback=on_status,
            overlay_callback=lambda s, m, sec: None,
        )

        with patch("psutil.process_iter", return_value=[]):
            result = service.start_recording()

        assert result is True
        assert service.is_recording() is True

    def test_start_recording_fails_when_priority_app_is_running(self) -> None:
        """start_recording returns False when a priority app is detected."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
            CaptureState,
        )

        status_calls: list[tuple[str, str]] = []

        def on_status(text: str, color: str) -> None:
            status_calls.append((text, color))

        config = AudioCaptureConfig(priority_apps=["zoom", "teams"])

        # Mock a process whose name contains "zoom"
        fake_proc = MagicMock()
        fake_proc.info = {"name": "zoom.exe", "pid": 1234}

        with patch("psutil.process_iter", return_value=[fake_proc]):
            with patch("audio2text.services._recorder.sd", create=True) as _mock_sd:
                service = AudioCaptureService(
                    config=config,
                    status_callback=on_status,
                    overlay_callback=lambda s, m, sec: None,
                )
                result = service.start_recording()

        assert result is False
        assert service.is_recording() is False
        assert service.state == CaptureState.IDLE
        # Should have emitted a warning status
        assert any("priority" in text.lower() or "orange" == color for text, color in status_calls)

    def test_start_recording_when_already_recording_returns_false(self) -> None:
        """Calling start while already recording is a no-op."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        config = AudioCaptureConfig(priority_apps=["zoom"])

        with patch("psutil.process_iter", return_value=[]):
            service = AudioCaptureService(
                config=config,
                status_callback=lambda t, c: None,
                overlay_callback=lambda s, m, sec: None,
            )
            first = service.start_recording()
            second = service.start_recording()

        assert first is True
        assert second is False

    def test_stop_recording_when_not_recording_is_noop(self) -> None:
        """stop_recording when not recording does nothing and returns None."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        config = AudioCaptureConfig()
        service = AudioCaptureService(
            config=config,
            status_callback=lambda t, c: None,
            overlay_callback=lambda s, m, sec: None,
        )
        result = service.stop_recording()
        assert result is None

    def test_stop_recording_saves_audio_segment(self) -> None:
        """stop_recording returns an AudioSegment when audio was captured."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        config = AudioCaptureConfig(sample_rate=16000, buffer_size=128)

        # Build a proper fake InputStream that behaves like sounddevice
        fake_stream = MagicMock()
        fake_stream.active = True
        # Each read returns 128 samples of fake float32 data
        recording_data = np.zeros(128, dtype=np.float32)

        read_count = [0]

        def fake_read(frames):
            read_count[0] += 1
            if read_count[0] > 10:
                raise StopIteration  # Stop the recording loop
            return (recording_data.copy(), False)

        fake_stream.read = fake_read

        with patch("psutil.process_iter", return_value=[]):
            with patch("audio2text.services._recorder.sd.InputStream", return_value=fake_stream):
                import soundfile as sf

                with patch.object(sf, "write") as _mock_sf_write:
                    service = AudioCaptureService(
                        config=config,
                        status_callback=lambda t, c: None,
                        overlay_callback=lambda s, m, sec: None,
                    )
                    # Start ensures the stream init is mocked
                    service.start_recording()
                    # Let the recording thread write some data
                    time.sleep(0.3)
                    # Stop the recording
                    result = service.stop_recording()

        assert result is not None
        assert result.data is not None
        assert result.sample_rate == 16000
        assert result.channels == 1

    def test_stop_recording_cleans_up_stream(self) -> None:
        """After stopping, the input stream is closed and set to None."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
            CaptureState,
        )

        config = AudioCaptureConfig(sample_rate=16000, buffer_size=128)

        fake_stream = MagicMock()
        fake_stream.active = True
        fake_stream.read.return_value = (np.zeros(128, dtype=np.float32), False)

        read_count = [0]

        def limited_read(frames):
            read_count[0] += 1
            if read_count[0] > 5:
                raise StopIteration
            return (np.zeros(128, dtype=np.float32), False)

        fake_stream.read = limited_read

        with patch("psutil.process_iter", return_value=[]):
            with patch("audio2text.services._recorder.sd.InputStream", return_value=fake_stream):
                import soundfile as sf

                with patch.object(sf, "write"):
                    service = AudioCaptureService(
                        config=config,
                        status_callback=lambda t, c: None,
                        overlay_callback=lambda s, m, sec: None,
                    )
                    service.start_recording()
                    time.sleep(0.2)
                    service.stop_recording()

        # After stop, the stream should have been stopped and closed
        fake_stream.stop.assert_called_once()
        fake_stream.close.assert_called_once()
        assert service.state == CaptureState.IDLE

    def test_get_duration_returns_elapsed_recording_time(self) -> None:
        """get_duration returns the time since recording started."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        config = AudioCaptureConfig(sample_rate=16000, buffer_size=128)

        fake_stream = MagicMock()
        fake_stream.active = True
        fake_stream.read.return_value = (np.zeros(128, dtype=np.float32), False)

        with patch("psutil.process_iter", return_value=[]):
            with patch("audio2text.services._recorder.sd.InputStream", return_value=fake_stream):
                service = AudioCaptureService(
                    config=config,
                    status_callback=lambda t, c: None,
                    overlay_callback=lambda s, m, sec: None,
                )
                service.start_recording()
                time.sleep(0.15)
                duration = service.get_duration()

        assert duration > 0.0
        assert duration < 5.0


class TestAudioCaptureServiceCallbacks:
    """Tests for callback invocation during recording lifecycle."""

    def test_status_callback_fired_on_start(self) -> None:
        """Status callback is invoked when recording starts."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        status_calls: list[tuple[str, str]] = []

        def on_status(text: str, color: str) -> None:
            status_calls.append((text, color))

        config = AudioCaptureConfig()

        with patch("psutil.process_iter", return_value=[]):
            with patch("audio2text.services._recorder.sd.InputStream") as mock_stream_cls:
                mock_stream = MagicMock()
                mock_stream.active = True
                mock_stream.read.return_value = (np.zeros(128, dtype=np.float32), False)
                mock_stream_cls.return_value = mock_stream

                service = AudioCaptureService(
                    config=config,
                    status_callback=on_status,
                    overlay_callback=lambda s, m, sec: None,
                )
                service.start_recording()

        assert len(status_calls) > 0
        # Start should emit a "recording" status
        assert any("recording" in text.lower() or "green" == color for text, color in status_calls)

    def test_overlay_callback_fired_on_start(self) -> None:
        """Overlay callback is invoked when recording starts."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        overlay_calls: list[tuple[str, int, int]] = []

        def on_overlay(state: str, minutes: int, seconds: int) -> None:
            overlay_calls.append((state, minutes, seconds))

        config = AudioCaptureConfig()

        with patch("psutil.process_iter", return_value=[]):
            with patch("audio2text.services._recorder.sd.InputStream") as mock_stream_cls:
                mock_stream = MagicMock()
                mock_stream.active = True
                mock_stream.read.return_value = (np.zeros(128, dtype=np.float32), False)
                mock_stream_cls.return_value = mock_stream

                service = AudioCaptureService(
                    config=config,
                    status_callback=lambda t, c: None,
                    overlay_callback=on_overlay,
                )
                service.start_recording()

        assert len(overlay_calls) > 0

    def test_overlay_callback_fired_on_stop_processing(self) -> None:
        """Overlay callback shows 'processing' state when recording stops."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        overlay_calls: list[tuple[str, int, int]] = []

        def on_overlay(state: str, minutes: int, seconds: int) -> None:
            overlay_calls.append((state, minutes, seconds))

        config = AudioCaptureConfig(sample_rate=16000, buffer_size=128)

        fake_stream = MagicMock()
        fake_stream.active = True
        fake_stream.read.return_value = (np.zeros(128, dtype=np.float32), False)

        read_count = [0]

        def limited_read(frames):
            read_count[0] += 1
            if read_count[0] > 5:
                raise StopIteration
            return (np.zeros(128, dtype=np.float32), False)

        fake_stream.read = limited_read

        with patch("psutil.process_iter", return_value=[]):
            with patch("audio2text.services._recorder.sd.InputStream", return_value=fake_stream):
                import soundfile as sf

                with patch.object(sf, "write"):
                    service = AudioCaptureService(
                        config=config,
                        status_callback=lambda t, c: None,
                        overlay_callback=on_overlay,
                    )
                    service.start_recording()
                    time.sleep(0.2)
                    service.stop_recording()

        # Verify processing state was emitted
        processing_calls = [
            (s, m, sec) for s, m, sec in overlay_calls if s == "processing"
        ]
        assert len(processing_calls) > 0


class TestAudioCaptureServiceThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_start_recording_only_one_succeeds(self) -> None:
        """When two threads try to start simultaneously, only one succeeds."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        config = AudioCaptureConfig(priority_apps=["zoom"])
        results: list[bool] = []

        with patch("psutil.process_iter", return_value=[]):
            service = AudioCaptureService(
                config=config,
                status_callback=lambda t, c: None,
                overlay_callback=lambda s, m, sec: None,
            )

        def try_start() -> None:
            results.append(service.start_recording())

        with patch("psutil.process_iter", return_value=[]):
            t1 = threading.Thread(target=try_start)
            t2 = threading.Thread(target=try_start)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        # Exactly one should succeed
        assert sum(results) == 1


class TestAudioCaptureServiceStateTransitions:
    """Tests for state machine transitions."""

    def test_state_transitions_idle_to_recording(self) -> None:
        """State transitions from IDLE to RECORDING on start."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
            CaptureState,
        )

        config = AudioCaptureConfig()

        with patch("psutil.process_iter", return_value=[]):
            with patch("audio2text.services._recorder.sd.InputStream") as mock_cls:
                mock_stream = MagicMock()
                mock_stream.active = True
                mock_stream.read.return_value = (np.zeros(128, dtype=np.float32), False)
                mock_cls.return_value = mock_stream

                service = AudioCaptureService(
                    config=config,
                    status_callback=lambda t, c: None,
                    overlay_callback=lambda s, m, sec: None,
                )
                assert service.state == CaptureState.IDLE
                service.start_recording()
                assert service.state == CaptureState.RECORDING

    def test_max_recording_time_enforced(self) -> None:
        """Recording stops automatically when max time is exceeded."""
        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        # Set a very short max time so the test is fast
        config = AudioCaptureConfig(max_recording_time=0.1, buffer_size=128)

        fake_stream = MagicMock()
        fake_stream.active = True
        fake_stream.read.return_value = (np.zeros(128, dtype=np.float32), False)

        with patch("psutil.process_iter", return_value=[]):
            with patch("audio2text.services._recorder.sd.InputStream", return_value=fake_stream):
                import soundfile as sf

                with patch.object(sf, "write"):
                    service = AudioCaptureService(
                        config=config,
                        status_callback=lambda t, c: None,
                        overlay_callback=lambda s, m, sec: None,
                    )
                    service.start_recording()
                    # Wait for the recording to auto-stop
                    time.sleep(0.4)
                    assert service.is_recording() is False
