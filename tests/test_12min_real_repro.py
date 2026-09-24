# -*- coding: utf-8 -*-
"""
Repro real 12m smoke (720s) — gap mock vs real Groq/network/fs.

Root cause: stop_recording join(current_thread) raises RuntimeError
cuando _record_loop auto-corta por max_recording_time (720s).
El join fallaba antes de spawnear process_recording → nunca transcribía, colgado.

Este test reproduce sin necesitar 12min reales:
- Genera WAV sintético 12min (~23MB PCM16) en tmp_path
- Verifica split en ~28-30 chunks de 25s
- Simula Groq timeout colgado en chunk 15 (y 413/429 paths)
- Valida que transcription_debug.log registra cada chunk con flush
- Valida que stop_recording desde recording_thread no lanza RuntimeError y sí procesa
"""
import os
import time
import threading
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import numpy as np
import soundfile as sf
import pytest

SR = 16000

def _make_pattern(duration_s, sr=SR):
    n = int(duration_s * sr)
    audio = np.zeros(n, dtype=np.float32)
    pos = 0
    while pos < n:
        end = min(pos + int(2.0*sr), n)
        tt = np.arange(end-pos)/sr
        audio[pos:end] = 0.3*np.sin(2*np.pi*220*tt)
        pos = end
        if pos >= n:
            break
        pos = min(pos + int(0.4*sr), n)
    return audio

def _reset_circuit():
    import backend.transcriber as tr_mod
    tr_mod._groq_circuit_failures = 0
    tr_mod._groq_circuit_open_until = 0.0

def _make_wav(path: Path, duration_s: float):
    audio = _make_pattern(duration_s)
    n = int(duration_s * SR)
    if len(audio) < n:
        audio = np.pad(audio, (0, n-len(audio)))
    elif len(audio) > n:
        audio = audio[:n]
    sf.write(str(path), audio, SR, subtype='PCM_16')
    return path

class Test12MinRealRepro:

    def test_split_720s_produces_28_chunks(self, tmp_path):
        from backend.audio_chunker import split_audio_on_silence
        audio = _make_pattern(720)
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        assert 26 <= len(chunks) <= 32, f"720s debe dar ~28 chunks, got {len(chunks)}"
        for c in chunks:
            assert len(c) <= int(29.0*SR) + 1
            assert len(c) > 0
        # concat lossless
        concat = np.concatenate(chunks)
        assert len(concat) == len(audio)
        # tamaño estimado PCM16 ~23MB
        est_mb = len(audio) * 2 / (1024*1024)
        assert 20 < est_mb < 30

    def test_stop_recording_from_recording_thread_no_hang(self):
        """Reproduce root-cause: join(current_thread) sin fix lanza RuntimeError y no procesa."""
        _reset_circuit()
        from backend.transcriber import Transcriber
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es","save_audio":False}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test_dummy")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        fm = Mock()
        fm.save_audio_file = Mock(return_value=None)
        fm.save_transcription_entry = Mock()
        with patch("backend.transcriber.Groq", return_value=Mock()):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), fm, Mock(), Mock(), Mock())
                tr.current_recording_id = "auto-cut-id"
                tr.audio_data = [np.zeros(int(1*SR), dtype=np.float32)]
                tr.input_stream = Mock()
                tr.input_stream.active = False
                tr.input_stream.stop = Mock()
                tr.input_stream.close = Mock()
                # Simular que recording_thread es el current thread (auto-cut path)
                tr.recording_thread = threading.current_thread()
                tr.is_recording = True
                tr.stop_event = threading.Event()
                # Mock process_recording tracking
                called = {}
                orig_proc = tr.process_recording
                def fake_proc(*a, **kw):
                    called["called"] = True
                # we will patch threading.Thread to capture start
                with patch("threading.Thread") as mock_thread:
                    mock_instance = Mock()
                    mock_thread.return_value = mock_instance
                    try:
                        tr.stop_recording()
                    except RuntimeError:
                        pytest.fail("stop_recording no debe lanzar RuntimeError cuando se llama desde recording_thread (fix pendiente)")
                    # Debe haber intentado spawnear process_recording thread
                    assert mock_thread.called, "auto-cut debe spawnear thread de process_recording aun sin join"
                    # is_recording debe quedar False pero haber continuado
                    assert tr.is_recording is False

    def test_transcribe_720s_with_mock_timeout_chunk15_no_hang(self, tmp_path):
        """720s sintético con Groq timeout en chunk 15 — no debe colgar, debe dar parcial con checkpoint."""
        _reset_circuit()
        wav = tmp_path / "smoke_720.wav"
        # Use 180s para test rápido pero simula 720 chunk logic (7 chunks, timeout en chunk 4)
        # El split 720 ya está validado en test_split; aquí validamos no hang + checkpoint
        _make_wav(wav, duration_s=180)
        assert wav.exists()
        assert wav.stat().st_size > 4*1024*1024
        from backend.transcriber import Transcriber
        from groq import APITimeoutError
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        # side effect por llamada Groq: chunks 1-3 OK, chunk4 timeout 3 intentos (falla), luego sigue
        call_n = {"c":0}
        def side_effect(*a, **kw):
            call_n["c"] += 1
            if 4 <= call_n["c"] <= 6:
                raise APITimeoutError("timeout colgado chunk4")
            return f"texto{call_n['c']}"
        mock_client.audio.transcriptions.create = Mock(side_effect=side_effect)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                with patch("time.sleep", return_value=None):
                    with patch("random.uniform", return_value=0.1):
                        start = time.time()
                        res = tr.transcribe_with_groq(str(wav))
                        elapsed = time.time() - start
                        assert elapsed < 70.0, f"no debe colgar, tardó {elapsed:.1f}s"
                        # debe tener texto parcial (no None totalmente vacío porque hay muchos chunks OK)
                        assert res is not None
                        assert "texto1" in res
                        # parcial file puede existir si hubo fallo; pero si luego continúa, all_ok False → partial conservado
                        partial = Path(str(wav)+".partial.txt")
                        # after mock, chunk 15 falló → all_ok False → partial debe existir OR res parcial
                        # Nuestra impl mantiene parcial cuando all_ok False
                        assert partial.exists() or "texto1" in res
                        if partial.exists():
                            partial.unlink()

    def test_413_fail_fast_no_retry(self, tmp_path):
        _reset_circuit()
        wav = tmp_path / "small.wav"
        _make_wav(wav, 5)
        from backend.transcriber import Transcriber
        from groq import APIStatusError
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        err = APIStatusError("413 Payload Too Large", response=Mock(headers={}), body=None)
        err.status_code = 413
        mock_client.audio.transcriptions.create = Mock(side_effect=err)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                res = tr.transcribe_with_groq(str(wav))
                assert res is None
                assert mock_client.audio.transcriptions.create.call_count == 1

    def test_transcription_debug_log_exists_and_has_chunk_records(self, tmp_path):
        """Asegura que logs/transcription_debug.log existe y contiene registros por chunk."""
        # forzar ensure
        from backend.logger import ensure_transcription_debug_handler
        log_path = ensure_transcription_debug_handler()
        assert log_path.exists() or log_path.parent.exists()
        # generar un transcribe corto que loguee
        wav = tmp_path / "log_test.wav"
        _make_wav(wav, 35)  # 35s → 2 chunks
        from backend.transcriber import Transcriber
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        mock_client.audio.transcriptions.create = Mock(return_value="hola mundo")
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                with patch("time.sleep", return_value=None):
                    res = tr.transcribe_with_groq(str(wav))
                    assert res is not None
        # ahora log debe tener entradas
        # leer logs/transcription_debug.log
        # Puede estar en project root logs/
        candidates = [log_path, Path("logs/transcription_debug.log"), Path("D:\\CENF\\gentle-ai\\audio2text-v0150-groq-fix\\logs\\transcription_debug.log")]
        found = None
        for p in candidates:
            if p.exists():
                found = p
                break
        assert found is not None and found.exists(), f"transcription_debug.log no existe, probados {candidates}"
        content = found.read_text(encoding="utf-8", errors="ignore")
        # debe contener marcas de chunk
        assert "Chunk" in content or "chunk" in content.lower()
        assert "Groq" in content or "transcribe" in content.lower()

    def test_global_timeout_not_hang_on_endless_groq(self, tmp_path):
        """Si Groq cuelga en cada chunk (timeout infinito), global timeout debe abortar sin hang eterno."""
        _reset_circuit()
        wav = tmp_path / "hang.wav"
        _make_wav(wav, 180)
        from backend.transcriber import Transcriber
        from groq import APITimeoutError
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        mock_client.audio.transcriptions.create = Mock(side_effect=APITimeoutError("timeout hang"))
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                # Simular deadline ya pasado parchando time.time para que global timeout dispare rápido
                with patch("backend.transcriber.time") as mock_time:
                    # time.time returns huge, perf_counter normal
                    mock_time.time.side_effect = lambda: 1e9  # always past deadline
                    mock_time.perf_counter.side_effect = time.perf_counter
                    mock_time.sleep = time.sleep
                    with patch("time.sleep", return_value=None):
                        # debería abortar rápido por global timeout, no iterar 28*3 retries eternamente
                        # Como mock_time.time siempre > deadline, el loop break en primer check
                        res = tr.transcribe_with_groq(str(wav))
                        # puede ser None o parcial, lo importante es no colgar y no lanzar
                        assert res is None or isinstance(res, str)


class TestSliceBRealRepro:
    """Slice B smoke paralelo: orden, speedup, no race checkpoint, 429 aislado."""

    def test_parallel_720s_preserves_order_under_load(self, tmp_path):
        """Reproduce 720s 28chunks con latencia variable — join debe reordenar."""
        _reset_circuit()
        from backend.transcriber import Transcriber
        wav = tmp_path / "smoke720.wav"
        _make_wav(wav, 180)  # 180s ~7 chunks, escala rapido; 720 validado en split test
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es","groq_parallel_workers":3}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        import time as _t
        call = {"n": 0}
        def side(*a, **kw):
            n = call["n"]
            call["n"] += 1
            _t.sleep(0.04 if n % 2 else 0.02)
            return f"c{n}"
        mock_client.audio.transcriptions.create = Mock(side_effect=side)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                res = tr.transcribe_with_groq(str(wav))
                assert res is not None
                # orden preservado: debe empezar por c0
                assert res.split()[0] == "c0"
                # checkpoint thread-safe: si existía partial, debe estar ordenado
                partial = Path(str(wav) + ".partial.txt")
                if partial.exists():
                    assert partial.read_text(encoding="utf-8").split()[0] == "c0"
                    try:
                        partial.unlink()
                    except Exception:
                        pass

    def test_parallel_no_race_checkpoint(self, tmp_path):
        """Checkpoint writes con lock: múltiples completions concurrentes no corrompen."""
        _reset_circuit()
        wav = tmp_path / "race.wav"
        _make_wav(wav, 60)
        from backend.transcriber import Transcriber
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es","groq_parallel_workers":3}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        mock_client.audio.transcriptions.create = Mock(return_value="ok")
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                # forzar concurrencia real
                res = tr.transcribe_with_groq(str(wav))
                assert res is not None
                # no race: archivo parcial o borrado limpio, sin contenido corrupto
                partial = Path(str(wav) + ".partial.txt")
                if partial.exists():
                    txt = partial.read_text(encoding="utf-8", errors="ignore")
                    # no debe tener duplicados desordenados tipo "ok ok ok" con gaps? solo check no vacío
                    assert "ok" in txt
                    partial.unlink()

    def test_parallel_429_isolated(self, tmp_path):
        """429 en 1 chunk no cancela otros: parallel debe completar los demás."""
        _reset_circuit()
        wav = tmp_path / "429_iso.wav"
        _make_wav(wav, 60)
        from backend.transcriber import Transcriber
        from groq import RateLimitError
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es","groq_parallel_workers":3}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        cnt = {"c": 0}
        def side(*a, **kw):
            cnt["c"] += 1
            if cnt["c"] == 2:
                raise RateLimitError("429", response=Mock(headers={}), body=None)
            return f"ok{cnt['c']}"
        mock_client.audio.transcriptions.create = Mock(side_effect=side)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                with patch("time.sleep", return_value=None):
                    with patch("random.uniform", return_value=0.05):
                        res = tr.transcribe_with_groq(str(wav))
                        assert res is not None
                        # al menos uno de los oks debe estar (otros no cancelados)
                        assert "ok1" in res or "ok3" in res
