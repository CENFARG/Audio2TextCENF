"""
v0.15.8 blindaje anti-duplicación — tests single-owner.

- test_concurrent_process_recording_single_display: mismo recording_id + mismo audio -> solo 1 callback
- test_different_audio_allows_second: audios distintos -> 2 callbacks
"""
import threading
import time
import numpy as np
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

# v0.15.8: mock missing native deps si no están instaladas (permite correr en CI liviano)
def _ensure_mocks():
    for _m in ["sounddevice", "soundfile", "keyboard", "groq", "customtkinter", "pystray", "pyperclip", "pyautogui", "psutil", "requests", "keyring"]:
        if _m not in sys.modules:
            try:
                __import__(_m)
            except ImportError:
                sys.modules[_m] = MagicMock()
    if "groq" in sys.modules and not hasattr(sys.modules["groq"], "Groq"):
        sys.modules["groq"].Groq = MagicMock()
    if "sounddevice" in sys.modules and not hasattr(sys.modules["sounddevice"], "InputStream"):
        sys.modules["sounddevice"].InputStream = MagicMock
    ctk = sys.modules.get("customtkinter")
    if ctk is not None and not isinstance(getattr(ctk, "CTk", None), type):
        _dummy = type("CTk", (), {})
        for _cls in ["CTkFrame", "CTkLabel", "CTkButton", "CTkTextbox", "CTkTabview", "CTkScrollableFrame", "CTkToplevel", "CTkEntry", "CTkSwitch", "CTkCheckBox", "CTkOptionMenu", "CTkSegmentedButton", "CTkComboBox", "CTkRadioButton"]:
            if not hasattr(ctk, _cls):
                setattr(ctk, _cls, _dummy)
        ctk.CTk = _dummy

_ensure_mocks()


def _make_transcriber(mock_transcription_cb=None):
    from backend.transcriber import Transcriber

    config_manager = Mock()
    # default returns for various keys
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
    # avoid keyring warnings
    sound_manager = Mock()
    sound_manager.sound_start_recording = Mock()
    sound_manager.sound_stop_recording = Mock()
    sound_manager.sound_success = Mock()
    file_manager = Mock()
    file_manager.save_audio_file.return_value = "/tmp/fake.wav"
    file_manager.save_transcription_entry.return_value = True

    update_status = Mock()
    loc = Mock()
    loc.get_string.side_effect = lambda k, **kw: k

    # Patch Groq client and keyboard hooks to avoid side effects
    with patch("backend.transcriber.Groq", return_value=Mock()), \
         patch("backend.transcriber.keyboard"), \
         patch("backend.transcriber.sd"), \
         patch.object(Transcriber, "hotkey_listener", return_value=None):
        # Also patch hotkey thread start
        with patch("threading.Thread"):
            t = Transcriber(
                config_manager=config_manager,
                sound_manager=sound_manager,
                file_manager=file_manager,
                update_status_callback=update_status,
                transcription_callback=mock_transcription_cb or Mock(),
                localization_manager=loc,
                overlay_callback=None,
            )
            # prevent hotkey_thread auto-start side effects
            t.ejecutando = True
            # stub transcribe to return fixed text
            t.transcribe = Mock(return_value="hola mundo test")
            # ensure overlay queue exists
            return t


def test_concurrent_process_recording_single_display():
    """Mismo recording_id + mismo audio: solo 1 callback debe ejecutarse (process_lock + hash dedup)."""
    cb = Mock()
    tr = _make_transcriber(mock_transcription_cb=cb)
    tr.freq = 16000
    # crear snapshot que dure > MIN_AUDIO_DURATION (0.5s) -> 16000*1 = 1s
    chunk = np.zeros((1024, 1), dtype=np.float32)
    # construir snapshot de ~1 segundo: 16 chunks
    audio_snapshot = [chunk for _ in range(16)]
    rid = "test-id-123"

    # Necesitamos que process_lock y hash funcionen: llamar concurrentemente
    # Patch sf.write to avoid file I/O
    with patch("backend.transcriber.sf.write"), \
         patch("tempfile.NamedTemporaryFile") as mock_tmp:
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/fake_temp.wav"
        # Patch os.path.exists / unlink / open not needed for transcribe mocked
        with patch("os.path.exists", return_value=False):
            with patch("os.unlink"):
                # Lanzar 2 threads concurrentes con mismo rid y mismo snapshot
                t1 = threading.Thread(target=tr.process_recording, args=(rid, audio_snapshot))
                t2 = threading.Thread(target=tr.process_recording, args=(rid, audio_snapshot))
                t1.start()
                t2.start()
                t1.join(timeout=5)
                t2.join(timeout=5)
                # Dar tiempo a que process_lock se libere si hubo secuencialidad
                time.sleep(0.3)
                # Solo uno debe haber llamado transcription_callback
                assert cb.call_count == 1, f"expected 1 callback, got {cb.call_count} — process_lock/hash dedup failed"
                # Verificar que el segundo fue descartado por lock o hash
                # El primero debe haber completado; el segundo no debió procesar


def test_different_audio_allows_second():
    """Audios distintos (hash diferente) con distinto recording_id -> deben pasar ambos."""
    cb = Mock()
    tr = _make_transcriber(mock_transcription_cb=cb)
    tr.freq = 16000

    chunk_a = np.zeros((1024, 1), dtype=np.float32)
    chunk_b = np.ones((1024, 1), dtype=np.float32) * 0.5
    snap_a = [chunk_a for _ in range(16)]
    snap_b = [chunk_b for _ in range(16)]
    rid_a = "id-a"
    rid_b = "id-b"

    # Necesita llamada secuencial con tiempo >2s entre hashes diferentes? No, hashes distintos
    # nunca deben ser bloqueados. Los hacemos secuenciales para evitar lock contention.
    with patch("backend.transcriber.sf.write"), \
         patch("tempfile.NamedTemporaryFile") as mock_tmp:
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/fake_temp2.wav"
        with patch("os.path.exists", return_value=False):
            with patch("os.unlink"):
                tr.process_recording(rid_a, snap_a)
                # pequeño sleep para que libere lock
                time.sleep(0.2)
                tr.process_recording(rid_b, snap_b)
                time.sleep(0.2)
                assert cb.call_count == 2, f"expected 2 callbacks for different audio, got {cb.call_count}"
                # Verificar que cada llamada recibió el texto esperado
                assert cb.call_args_list[0][0][0] == "hola mundo test"
                assert cb.call_args_list[1][0][0] == "hola mundo test"
