"""Double-paste repro tests (user report: transcription pasted twice, back to back).

Chain under test:
    Transcriber.transcription_callback (backend/transcriber.py:99, single site per
    successful process_recording) -> App.display_transcription (ui/app.py, v0.15.8
    duplicate guards) -> App._safe_display_transcription_on_main_thread
    (pyperclip.copy + auto-paste pyautogui ctrl+v).

Hypotheses (each with a deterministic repro):
  (a) callback registered twice (config save / reload paths)  -> refuted by tests,
      pinned here as idempotency guards.
  (b) dedup guard bypass: near-duplicate text (whitespace-only difference) and
      concurrent same-text display calls racing the check-then-set guard.
  (c) auto-paste automation firing twice per display event / for duplicated
      dispatch — pinned to single-fire per identical text within a cooldown.
  (d) double process_recording spawn from a stop_recording race between the
      recording thread (auto-cut, no recording_lock) and the hotkey thread
      (holds recording_lock) -> two transcription callbacks.

UI-level tests run the REAL App.display_transcription /
App._safe_display_transcription_on_main_thread against a headless harness
(no Tk). Transcriber-level tests run the real Transcriber with mocked
hardware/API, following tests/test_no_duplicate_transcription.py conventions.
"""

import inspect
import logging
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

APP_SOURCE: str | None = None  # populated lazily by _app_source()


def _ensure_mocks():
    """Mock missing native deps so ui.app / backend.transcriber import headless."""
    for _m in [
        "sounddevice",
        "soundfile",
        "keyboard",
        "groq",
        "customtkinter",
        "pystray",
        "pyperclip",
        "pyautogui",
        "psutil",
        "requests",
        "keyring",
    ]:
        if _m not in sys.modules:
            try:
                __import__(_m)
            except ImportError:
                sys.modules[_m] = MagicMock()
    groq_mod = cast(Any, sys.modules.get("groq"))
    if groq_mod is not None and not hasattr(groq_mod, "Groq"):
        groq_mod.Groq = MagicMock()
    sd_mod = cast(Any, sys.modules.get("sounddevice"))
    if sd_mod is not None and not hasattr(sd_mod, "InputStream"):
        sd_mod.InputStream = MagicMock
    ctk = sys.modules.get("customtkinter")
    if ctk is not None and not isinstance(getattr(ctk, "CTk", None), type):
        _dummy = type("CTk", (), {})
        for _cls in [
            "CTkFrame",
            "CTkLabel",
            "CTkButton",
            "CTkTextbox",
            "CTkTabview",
            "CTkScrollableFrame",
            "CTkToplevel",
            "CTkEntry",
            "CTkSwitch",
            "CTkCheckBox",
            "CTkOptionMenu",
            "CTkSegmentedButton",
            "CTkComboBox",
            "CTkRadioButton",
        ]:
            if not hasattr(ctk, _cls):
                setattr(ctk, _cls, _dummy)
        _ctk_root = "CTk"
        setattr(ctk, _ctk_root, _dummy)


_ensure_mocks()


def _app_source():
    global APP_SOURCE
    if APP_SOURCE is None:
        import ui.app as app_module

        APP_SOURCE = inspect.getsource(app_module)
    return APP_SOURCE


# ---------------------------------------------------------------------------
# UI harness: real App methods on a duck-typed host (no Tk loop).
# ---------------------------------------------------------------------------


class _CfgStub:
    """Minimal config_manager double for the display/paste methods."""

    def __init__(self, values=None):
        self._values = dict(values or {})

    def get(self, key, default=None):
        return self._values.get(key, default)


class _DisplayHarness:
    """Headless host binding the REAL App display/paste methods.

    ``gate_state_setter`` turns ``last_transcription_text`` into a gated
    property: the FIRST writer blocks until a SECOND writer arrives (or a
    3s timeout). This deterministically recreates the check-then-set race
    window in display_transcription's duplicate guards: both threads have
    already PASSED the guards when either records its state.
    """

    # Bound dynamically in _bind_app_methods (real App methods).
    display_transcription: Callable[..., Any]
    _safe_display_transcription_on_main_thread: Callable[..., Any]

    def __init__(self, gate_state_setter=False, auto_paste=True):
        # v0.15.8 guard state (same attributes App.__init__ seeds)
        self.last_transcription_time = 0.0
        self._text_state = ""
        self.last_transcription_hash = None
        self.logger = logging.getLogger("test_double_paste")
        self.config_manager = _CfgStub(
            {
                "show_transcription_panel": False,
                "auto_paste_text": auto_paste,
            }
        )
        self.transcriber = Mock()
        self.transcriber.last_block_display = None
        self.scheduled = []
        self.last_auto_paste_monotonic = 0.0
        self.display_guard_lock = threading.Lock()
        self._gate_enabled = gate_state_setter
        self._setter_arrivals = 0
        self._second_setter = threading.Event()

    # -- gated state (deterministic race interposition) --------------------
    @property
    def last_transcription_text(self):
        return self._text_state

    @last_transcription_text.setter
    def last_transcription_text(self, value):
        if self._gate_enabled:
            self._setter_arrivals += 1
            if self._setter_arrivals == 1:
                # Hold the race window open until the rival thread also
                # passed every guard and tries to record its state.
                self._second_setter.wait(timeout=3.0)
            else:
                self._second_setter.set()
        self._text_state = value

    # -- Tk doubles --------------------------------------------------------
    def after(self, ms, fn, *args):
        self.scheduled.append((ms, fn, args))

    def run_scheduled(self):
        """Drain the scheduled queue, running newly scheduled items too."""
        while self.scheduled:
            _ms, fn, args = self.scheduled.pop(0)
            fn(*args)


def _bind_app_methods(harness):
    """Bind the REAL App display chain onto the harness."""
    import ui.app as app_module

    harness.display_transcription = app_module.App.display_transcription.__get__(harness)
    harness._safe_display_transcription_on_main_thread = (
        app_module.App._safe_display_transcription_on_main_thread.__get__(harness)
    )
    return harness


def _make_harness(gate_state_setter=False):
    return _bind_app_methods(_DisplayHarness(gate_state_setter=gate_state_setter))


# ---------------------------------------------------------------------------
# Transcriber fixture (stop-race repro): real Transcriber, no mic / no API.
# ---------------------------------------------------------------------------


class _GateEvent(threading.Event):
    """threading.Event double: the FIRST set() blocks until a SECOND set().

    Deterministically recreates the stop_recording race: two threads both
    passed the ``is_recording`` check and both reached ``stop_event.set()``
    (the flip happens AFTER set() in the legacy code, so the second thread
    still sees ``is_recording == True``).
    """

    def __init__(self):
        super().__init__()
        self._second = threading.Event()
        self.arrivals = 0

    def set(self):
        self.arrivals += 1
        if self.arrivals == 1:
            self._second.wait(timeout=3.0)
        else:
            self._second.set()
        super().set()

    def clear(self):
        super().clear()


def _make_transcriber(callback=None):
    from backend.transcriber import Transcriber

    config_manager = Mock()

    def _get(key, default=None):
        defaults = {
            "hotkey": "f12",
            "record_mode": "toggle",
            "audio_priority_apps": [],
            "max_recording_time": 300,
            "groq_api_key": "gsk_test",
            "nvidia_enabled": False,
            "transcription_language": "es",
            "default_language": "es",
            "blocks": {},
            "save_audio": False,
            "save_logs": False,
        }
        return defaults.get(key, default)

    config_manager.get.side_effect = _get
    config_manager.get_groq_api_key_from_env.return_value = "gsk_test"

    with patch("backend.transcriber.Groq", return_value=Mock()), patch(
        "backend.transcriber.NvidiaASR"
    ), patch("backend.transcriber.keyboard"), patch("backend.transcriber.sd"), patch.object(
        Transcriber, "hotkey_listener", return_value=None
    ), patch(
        "threading.Thread"
    ):
        tr = Transcriber(
            config_manager=config_manager,
            sound_manager=Mock(),
            file_manager=Mock(),
            update_status_callback=Mock(),
            transcription_callback=callback or Mock(),
            localization_manager=Mock(),
            overlay_callback=None,
        )
    # Thread patch is scoped to construction only: worker threads created by
    # the test itself (and by stop_recording) are REAL threads.
    return tr


# ---------------------------------------------------------------------------
# Hypothesis (a): callback registration must be idempotent.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCallbackRegistrationIdempotent:
    """transcription_callback is stored once and never re-registered."""

    def test_reload_client_and_hotkey_change_keep_same_callback(self):
        cb = Mock()
        tr = _make_transcriber(callback=cb)
        before = tr.transcription_callback

        with patch("backend.transcriber.Groq", return_value=Mock()), patch(
            "backend.transcriber.NvidiaASR"
        ), patch("backend.transcriber.keyboard"):
            tr.reload_client()
            tr.update_hotkey("f10")

        assert tr.transcription_callback is before

    def test_app_module_has_exactly_one_transcriber_instantiation(self):
        """save_config reloads clients but must never build a second Transcriber."""
        assert _app_source().count("= Transcriber(") == 1

    def test_single_callback_call_single_display_event(self):
        """One transcription -> exactly one display dispatch (hypothesis c baseline)."""
        h = _make_harness()
        with patch("ui.app.pyperclip") as mock_clip, patch("ui.app.pyautogui") as mock_gui:
            h.display_transcription("una sola vez")
            h.run_scheduled()

        assert mock_clip.copy.call_count == 1
        assert mock_gui.hotkey.call_count == 1
        assert mock_gui.hotkey.call_args == (("ctrl", "v"),)


# ---------------------------------------------------------------------------
# Hypothesis (b): dedup guard bypasses.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDisplayDedupGuard:
    def test_identical_text_twice_is_displayed_once(self):
        h = _make_harness()
        with patch("ui.app.pyperclip"), patch("ui.app.pyautogui") as mock_gui:
            h.display_transcription("hola mundo")
            h.display_transcription("hola mundo")
            h.run_scheduled()

        assert mock_gui.hotkey.call_count == 1

    def test_near_duplicate_whitespace_only_text_is_displayed_once(self):
        """Same content with whitespace differences must not paste twice (RED)."""
        h = _make_harness()
        with patch("ui.app.pyperclip"), patch("ui.app.pyautogui") as mock_gui:
            h.display_transcription("hola mundo")
            h.display_transcription("hola mundo \n")
            h.run_scheduled()

        assert mock_gui.hotkey.call_count == 1, (
            "near-duplicate (whitespace-only) text bypassed the hash guard "
            f"and pasted {mock_gui.hotkey.call_count} times"
        )

    def test_different_texts_both_paste(self):
        """Different content is legitimate: both must be displayed and pasted."""
        h = _make_harness()
        with patch("ui.app.pyperclip"), patch("ui.app.pyautogui") as mock_gui:
            h.display_transcription("primer texto")
            h.display_transcription("segundo texto distinto")
            h.run_scheduled()

        assert mock_gui.hotkey.call_count == 2

    def test_same_text_after_hash_window_expiry_pastes_again(self):
        """The 10s hash window is finite: same text much later must paste again.

        Both dedup clocks advance together in the real app, so the test ages
        the display hash window AND the paste cooldown before re-displaying.
        """
        h = _make_harness()
        with patch("ui.app.pyperclip"), patch("ui.app.pyautogui") as mock_gui:
            h.display_transcription("texto repetido tarde")
            h.run_scheduled()
            h.last_transcription_time = time.time() - 30.0  # display window expiry
            h.last_auto_paste_monotonic = time.monotonic() - 60.0  # paste cooldown expiry
            h.display_transcription("texto repetido tarde")
            h.run_scheduled()

        assert mock_gui.hotkey.call_count == 2

    def test_concurrent_same_text_display_pastes_once(self):
        """Two threads racing the check-then-set guard -> one paste (RED).

        The gate holds the guard's race window open: both threads pass every
        guard before either records its state. Without synchronization both
        dispatch a paste; with a guarded critical section only the first does.
        """
        h = _make_harness(gate_state_setter=True)
        threads = [
            threading.Thread(target=h.display_transcription, args=("texto en carrera",))
            for _ in range(2)
        ]
        with patch("ui.app.pyperclip"), patch("ui.app.pyautogui") as mock_gui:
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5.0)
            assert not any(t.is_alive() for t in threads), "display threads deadlocked"
            h.run_scheduled()

        assert mock_gui.hotkey.call_count == 1, (
            "concurrent same-text display calls raced the unsynchronized guard "
            f"and pasted {mock_gui.hotkey.call_count} times"
        )


# ---------------------------------------------------------------------------
# Hypothesis (c): auto-paste automation single-fire.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAutoPasteSingleFire:
    def test_duplicate_dispatch_same_text_pastes_once(self):
        """Two dispatches of the same text in quick succession -> one ctrl+v (RED).

        Covers the case where ANY upstream path double-dispatches
        _safe_display_transcription_on_main_thread: the paste automation is
        the last line of defense before the user sees the duplication.
        """
        h = _make_harness()
        with patch("ui.app.pyperclip"), patch("ui.app.pyautogui") as mock_gui:
            h._safe_display_transcription_on_main_thread("pegado dos veces")
            h._safe_display_transcription_on_main_thread("pegado dos veces")
            h.run_scheduled()

        assert mock_gui.hotkey.call_count == 1, (
            "auto-paste automation fired "
            f"{mock_gui.hotkey.call_count} times for identical back-to-back text"
        )

    def test_different_text_pastes_each_time(self):
        h = _make_harness()
        with patch("ui.app.pyperclip"), patch("ui.app.pyautogui") as mock_gui:
            h._safe_display_transcription_on_main_thread("primer pegado")
            h._safe_display_transcription_on_main_thread("segundo pegado distinto")
            h.run_scheduled()

        assert mock_gui.hotkey.call_count == 2

    def test_same_text_after_cooldown_pastes_again(self):
        h = _make_harness()
        with patch("ui.app.pyperclip"), patch("ui.app.pyautogui") as mock_gui:
            h._safe_display_transcription_on_main_thread("pegado tarde")
            # Simulate cooldown expiry (monotonic clock far in the past).
            h.last_auto_paste_monotonic = time.monotonic() - 60.0
            h._safe_display_transcription_on_main_thread("pegado tarde")
            h.run_scheduled()

        assert mock_gui.hotkey.call_count == 2


# ---------------------------------------------------------------------------
# Hypothesis (d): stop_recording race -> double process spawn.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStopRecordingSingleProcess:
    def _race_transcriber(self):
        """Recording session mid-flight with a gated stop_event."""
        tr = _make_transcriber()
        spawned_threads = []

        def _record_spawn(*args: Any, **kwargs: Any) -> None:
            spawned_threads.append(threading.current_thread())

        # Mock keeps the real process_recording body out of the race test;
        # we only count how many times stop_recording spawns it.
        tr.process_recording = Mock(side_effect=_record_spawn)
        tr.stop_event = _GateEvent()
        tr.is_recording = True
        tr.current_recording_id = "race-id"
        tr.input_stream = None
        with tr.audio_lock:
            tr.audio_data = [np.zeros((1024, 1), dtype=np.float32)]
        return tr, spawned_threads

    def _wait_spawned(self, spawned, expected, timeout_s=5.0):
        deadline = time.time() + timeout_s
        while len(spawned) < expected and time.time() < deadline:
            time.sleep(0.02)
        return len(spawned)

    def test_concurrent_stop_spawns_process_once(self):
        """Auto-cut thread + hotkey thread both entering stop_recording (RED).

        The gated stop_event holds the check->flip window open so both
        threads pass ``is_recording``; only a synchronized stop keeps the
        process spawn single.
        """
        tr, spawned = self._race_transcriber()
        threads = [threading.Thread(target=tr.stop_recording) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=6.0)
        assert not any(t.is_alive() for t in threads), "stop threads deadlocked"
        count = self._wait_spawned(spawned, 2)

        assert count == 1, (
            f"stop_recording race spawned {count} process_recording threads "
            "(double transcription -> double paste)"
        )

    def test_sequential_second_stop_is_noop(self):
        """Second stop after a completed stop must not spawn again (preserve)."""
        tr, spawned = self._race_transcriber()
        tr.stop_event = threading.Event()  # no gate: plain sequential calls
        tr.stop_recording()
        count = self._wait_spawned(spawned, 1)
        tr.stop_recording()
        time.sleep(0.1)

        assert count == 1
        assert len(spawned) == 1, f"expected 1 spawn, got {len(spawned)}"
