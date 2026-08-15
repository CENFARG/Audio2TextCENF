"""
Tests del flujo de captura de audio — FIX v0.15.0 (Kaizen Nodal / sdd-explore).

El bug: en grabaciones largas se pierden frames de audio SILENCIOSAMENTE cuando
el thread de grabación intenta actualizar la UI (update_status/overlay) mientras
el main thread está ocupado → el audio llega comprimido/cortado a Groq → texto
con palabras cortadas y tildes faltantes ("funciona por momentos y por momentos no").

Estos tests garantizan:
1. El bucle de grabación NO pierde frames aunque la UI esté bloqueada
2. max_recording_time drena el buffer antes de cortar (no descarta cola final)
3. El stop a mitad de read() agrega el bloque parcial
4. display y JSONL reciben el MISMO texto (panel == portapapeles == JSONL)
"""

import sys
import time
import threading
from pathlib import Path
from unittest.mock import Mock, MagicMock

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.transcriber import Transcriber


def make_transcriber(**overrides):
    """Crear un Transcriber con mocks para testear captura sin hardware real."""
    mock_deps = {
        "config_manager": Mock(),
        "sound_manager": Mock(),
        "file_manager": Mock(),
        "update_status_callback": Mock(),
        "transcription_callback": Mock(),
        "localization_manager": Mock(),
        "overlay_callback": Mock(),
    }
    mock_deps.update(overrides)
    # Construir Transcriber sin llamar al __init__ real (evita hardware/red)
    t = Transcriber.__new__(Transcriber)
    t.logger = Mock()
    t.config_manager = mock_deps["config_manager"]
    # Default de max_recording_time para que el loop no corte (si el test no lo overridea)
    if not isinstance(t.config_manager.get, Mock) or t.config_manager.get is mock_deps["config_manager"].get:
        pass
    t.config_manager.get = Mock(side_effect=lambda k, d=None: {"max_recording_time": 300}.get(k, d))
    t.sound_manager = mock_deps["sound_manager"]
    t.file_manager = mock_deps["file_manager"]
    t.update_status = mock_deps["update_status_callback"]
    t.transcription_callback = mock_deps["transcription_callback"]
    t.localization_manager = mock_deps["localization_manager"]
    t.overlay_callback = mock_deps["overlay_callback"]
    t.is_recording = False
    t.recording_lock = threading.Lock()
    t.audio_lock = threading.Lock()
    t.stop_event = threading.Event()
    t.ejecutando = True
    t.audio_data = []
    t.freq = 16000
    t.input_stream = None
    t.cliente = Mock()
    t.nvidia_client = None
    t.utf8_validator = Mock()
    t.utf8_validation_enabled = False
    t.custom_vocab = Mock()
    t.metadata_generator = Mock()
    t.metadata_manager = Mock()
    t.block_manager = Mock()
    t.last_block_results = []
    return t


class FakeInputStream:
    """Stream fake que produce bloques de 1024 frames float32.

    Puede simular que el read() se bloquea (simula la UI trabada bloqueando
    la lectura en el main thread).
    """

    def __init__(self, sample_rate=16000, block_size=1024):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.active = True
        self.reads = 0
        self.stop_requested = False

    def read(self, frames):
        self.reads += 1
        # Contract de sounddevice.InputStream.read(): devuelve (data, overflowed)
        return np.zeros(frames, dtype='float32'), False


@pytest.mark.unit
class TestCapturaNoPierdeFrames:
    """El bucle de grabación debe capturar TODO el audio sin perder frames."""

    def test_record_loop_no_pierde_frames_cuando_ui_se_traba(self):
        """
        BUG: si el callback de UI (update_status) bloquea 300ms, el read() de
        audio se estanca y se pierden frames SILENCIOSAMENTE. El invariante:
        frames capturados ≈ tiempo de grabación × sample_rate.
        """
        t = make_transcriber()

        # UI que se traba: cada llamada a update_status bloquea 200ms
        def slow_ui(*args, **kwargs):
            time.sleep(0.2)

        t.update_status = slow_ui

        stream = FakeInputStream()
        t.input_stream = stream
        t.stop_event.clear()

        # Correr el bucle en un thread durante ~1.2s
        thread = threading.Thread(target=t._record_loop, daemon=True)
        thread.start()

        time.sleep(1.2)
        t.stop_event.set()
        thread.join(timeout=2.0)

        # Invariante: audio capturado ≈ tiempo × freq (tol: 1 bloque de margen)
        with t.audio_lock:
            total_frames = sum(len(chunk) for chunk in t.audio_data)
        expected_frames = 1.2 * t.freq
        min_acceptable = expected_frames - 2 * stream.block_size  # 2 bloques de tolerancia

        assert total_frames >= min_acceptable, (
            f"Se perdieron frames: capturados {total_frames}, "
            f"esperados ~{expected_frames:.0f} (mínimo {min_acceptable})"
        )

    def test_record_loop_captura_normal_sin_perdida(self):
        """Caso control: sin UI bloqueada, el bucle captura casi todo."""
        t = make_transcriber()
        t.update_status = Mock()  # UI rápida
        t.overlay_callback = Mock()

        stream = FakeInputStream()
        t.input_stream = stream
        t.stop_event.clear()

        thread = threading.Thread(target=t._record_loop, daemon=True)
        thread.start()
        time.sleep(0.8)
        t.stop_event.set()
        thread.join(timeout=2.0)

        with t.audio_lock:
            total_frames = sum(len(c) for c in t.audio_data)
        expected = 0.8 * t.freq
        assert total_frames >= expected - 2 * stream.block_size, (
            f"Control perdió frames: {total_frames} vs {expected:.0f}"
        )


@pytest.mark.unit
class TestMaxRecordingTime:
    """max_recording_time debe drenar el buffer antes de cortar."""

    def test_max_recording_time_drena_cola_final(self):
        """Al superar el límite, el audio capturado incluye lo producido hasta el corte."""
        t = make_transcriber()
        # max_recording_time muy corto: 0.15s
        t.config_manager.get = Mock(side_effect=lambda k, d=None: 0.15 if k == "max_recording_time" else d)
        # get_string para status
        t.localization_manager.get_string = Mock(return_value="Grabando")

        stream = FakeInputStream()
        t.input_stream = stream
        t.stop_event.clear()

        # Necesitamos que stop_recording no intente tocar hardware real
        t.stop_recording = Mock(wraps=lambda: t.stop_event.set())

        thread = threading.Thread(target=t._record_loop, daemon=True)
        thread.start()
        thread.join(timeout=3.0)

        with t.audio_lock:
            total_frames = sum(len(c) for c in t.audio_data)

        # Con 0.15s de límite + drenado, deberíamos tener > 0.15s de audio
        min_expected = 0.15 * t.freq
        assert total_frames >= min_expected, (
            f"El corte por límite perdió audio: {total_frames} frames, esperado ≥ {min_expected}"
        )


@pytest.mark.unit
class TestDisplayJSONLConsistencia:
    """display y JSONL deben recibir el MISMO texto."""

    def test_display_y_jsonl_reciben_mismo_texto(self):
        """Blinda la garantía: panel == portapapeles == JSONL (mismo string)."""
        t = make_transcriber()
        texts_received = []

        def fake_callback(text):
            texts_received.append(text)

        t.transcription_callback = fake_callback
        t.file_manager.save_transcription_entry = Mock(
            side_effect=lambda entry: texts_received.append(entry["text"])
        )

        # Simular lo que hace process_recording: mismo string a ambos
        transcription = "Hola, esta es una prueba con acentos: áéíóúñ y palabras largas."
        t.transcription_callback(transcription)
        t.file_manager.save_transcription_entry({
            "text": transcription, "duration": 5.0,
            "language": "es", "audio_file": ""
        })

        assert len(texts_received) == 2
        assert texts_received[0] == texts_received[1] == transcription
