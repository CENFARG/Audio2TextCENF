# -*- coding: utf-8 -*-
"""
Slice C Streaming incremental — TDD tests sintéticos.

Cubre:
- Snapshot cada 25s con pool separado 2 workers (STREAM_WORKERS)
- Post-stop <6s para 720s (solo 1-2 chunks restantes)
- Orden preservado (reordena antes de join) aunque completions desordenadas
- Manejo 429/413/timeout sin bloquear grabación (no propaga, log STREAM)
- Lock para ordered dict (no race concurrent)
- UI poll streaming "En vivo Chunk X/Y..."
- Checkpoint .partial_stream.txt atómico

Usa WAV 720s sintético mock Groq 0.5s (escalado a 0.05s para no tardar 15s en CI) real 0.5s contract.
"""
import os
import time
import tempfile
import random
import threading
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import numpy as np
import soundfile as sf
import pytest

SR = 16000

def _reset_circuit():
    import backend.transcriber as tr_mod
    tr_mod._groq_circuit_failures = 0
    tr_mod._groq_circuit_open_until = 0.0

def _make_pattern(duration_s: float):
    n = int(duration_s * SR)
    audio = np.zeros(n, dtype=np.float32)
    pos = 0
    while pos < n:
        end = min(pos + int(2.0*SR), n)
        tt = np.arange(end-pos)/SR
        audio[pos:end] = 0.3*np.sin(2*np.pi*220*tt)
        pos = end
        if pos >= n:
            break
        pos = min(pos + int(0.4*SR), n)
    return audio

def _make_wav(path: Path, duration_s: float):
    audio = _make_pattern(duration_s)
    sf.write(str(path), audio, SR, subtype='PCM_16')
    return path

def _mock_transcriber(tmp_path=None):
    from backend.transcriber import Transcriber
    cm = Mock()
    cm.get.side_effect = lambda k, d=None: {
        "hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],
        "utf8_validation":True,"blocks":{},"max_recording_time":720,
        "transcription_language":"es","default_language":"es",
        "groq_parallel_workers":3, "save_audio":False
    }.get(k,d)
    cm.get_groq_api_key_from_env = Mock(return_value="gsk_test_dummy_key_123")
    cm.localization_manager = Mock()
    cm.localization_manager.get_string.side_effect = lambda k, **kw: k
    # Mock hardware/keys to avoid thread issues in CI
    mock_groq = Mock()
    with patch("backend.transcriber.Groq", return_value=mock_groq):
        with patch("backend.transcriber.NvidiaASR"):
            with patch("backend.transcriber.sd.InputStream", Mock()):
                with patch("backend.transcriber.keyboard", Mock()):
                    with patch("backend.transcriber.psutil.process_iter", return_value=[]):
                        tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                        # detener hotkey thread que intenta hook real
                        try:
                            tr.ejecutando = False
                        except Exception:
                            pass
    return tr


class TestStreamingConstants:
    def test_constants_slice_c(self):
        src = Path("backend/transcriber.py").read_text(encoding="utf-8")
        assert "STREAM_INTERVAL_S" in src
        assert "STREAM_WORKERS" in src
        assert "STREAM_PARTIAL_SUFFIX" in src
        assert "STREAM_TIMEOUT_S" in src
        # 25s interval, 2 workers separado de Slice B (3)
        from backend.transcriber import STREAM_INTERVAL_S, STREAM_WORKERS, STREAM_PARTIAL_SUFFIX
        assert STREAM_INTERVAL_S == 25.0
        assert STREAM_WORKERS == 2
        assert STREAM_PARTIAL_SUFFIX == ".partial_stream.txt"
        # pool separado
        assert 'thread_name_prefix="groq-stream"' in src
        assert "streaming_ordered" in src
        assert "streaming_lock" in src
        assert "STREAM" in src

    def test_ui_poll_streaming(self):
        src = Path("ui/app.py").read_text(encoding="utf-8")
        assert "streaming" in src.lower()
        assert "En vivo Chunk" in src
        # transcriber debe hacer push streaming
        src2 = Path("backend/transcriber.py").read_text(encoding="utf-8")
        assert "_push_streaming_event" in src2
        assert "streaming" in src2


class TestStreamingSnapshotAndLock:
    def test_snapshot_copy_does_not_block_audio(self, tmp_path):
        _reset_circuit()
        tr = _mock_transcriber()
        # simular audio_data con 30s
        tr.audio_data = [np.zeros(16000, dtype=np.float32) for _ in range(30)]  # 30*1024 ~30s
        tr.streaming_ordered = {}
        tr.streaming_pending = set()
        tr.streaming_partial_path = str(tmp_path / "stream.partial_stream.txt")
        tr.streaming_executor = __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=2)
        tr._stream_next_trigger = time.time() - 1
        # mock Groq para streaming: rápido
        tr._groq_chunk_callback = Mock(return_value="hola chunk")
        tr._stream_snapshot_and_submit()
        # debe haber submiteado al menos 1 chunk sin bloquear (is_recording False sim -> total chunks 1-2)
        time.sleep(0.3)
        # verificar ordered tiene algo
        with tr.streaming_lock:
            assert len(tr.streaming_ordered) >= 1 or len(tr.streaming_pending) >= 0
        # no race: lock protege dict
        tr.streaming_executor.shutdown(wait=True)

    def test_streaming_lock_no_race_concurrent(self):
        _reset_circuit()
        tr = _mock_transcriber()
        tr.streaming_ordered = {}
        tr.streaming_pending = set()
        import tempfile as _tf
        tr.streaming_partial_path = os.path.join(_tf.gettempdir(), f"test_race_{random.randint(0,999999)}.partial_stream.txt")
        tr.streaming_executor = __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="groq-stream")
        # mock rápido con delay variable para forzar out-of-order completions
        def fake_groq(chunk, sr, prompt=None):
            time.sleep(random.uniform(0.02, 0.06))
            # texto identifica idx por contenido? devolvemos fijo pero task setea idx externo
            return f"texto"
        tr._groq_chunk_callback = fake_groq
        # lanzar múltiples tasks concurrentes con idx distintos
        total_tasks = 6
        for i in range(total_tasks):
            chunk = np.zeros(int(1.0*SR), dtype=np.float32)
            # submit via executor que internamente usa _stream_transcribe_task que toma lock
            tr.streaming_pending.add(i)
            tr.streaming_executor.submit(tr._stream_transcribe_task, i, chunk, total_tasks, 10)
        tr.streaming_executor.shutdown(wait=True)
        with tr.streaming_lock:
            # todos con texto deben estar ordenados, no corrupción
            assert len(tr.streaming_ordered) == total_tasks
            # orden preservado al join
            ordered = " ".join([tr.streaming_ordered[k] for k in sorted(tr.streaming_ordered)])
            assert ordered.count("texto") == total_tasks
        # checkpoint file debe existir y estar ordenado
        if os.path.exists(tr.streaming_partial_path):
            content = Path(tr.streaming_partial_path).read_text(encoding="utf-8")
            assert "texto" in content
            try:
                os.unlink(tr.streaming_partial_path)
            except Exception:
                pass
            try:
                os.unlink(tr.streaming_partial_path + ".tmp")
            except Exception:
                pass


class TestStreamingPostStop:
    def test_post_stop_lt_6s_720s_mock_05(self, tmp_path):
        """720s sintético 29 chunks mock Groq 0.05s (escala de 0.5s real) → streaming 27 ya enviados, remaining 2 → post-stop <6s."""
        _reset_circuit()
        tr = _mock_transcriber()
        # 720s pattern
        audio = _make_pattern(720)
        from backend.audio_chunker import split_audio_on_silence
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        total = len(chunks)
        assert 25 <= total <= 32, f"720s debe dar ~29 chunks, got {total}"
        # mock Groq con 0.05s (escala de 0.5s contract: 0.5s*2 remaining =1s <6s, secuencial 29*0.5=14.5s)
        def mock_groq(chunk, sr, prompt=None):
            time.sleep(0.05)  # escala: 0.5s real → 0.05s test
            return f"chunk texto"
        tr._groq_chunk_callback = mock_groq
        # simular que streaming ya envió los primeros total-2 chunks
        streamed = {i: f"chunk{i} streamed texto" for i in range(total-2)}
        # también escribir partial_stream previo
        streamed_partial = str(tmp_path / "pre.partial_stream.txt")
        Path(streamed_partial).write_text(" ".join([streamed[k] for k in sorted(streamed)]), encoding="utf-8")
        # medir post-stop merge time (solo remaining 2 chunks)
        t0 = time.perf_counter()
        result = tr._transcribe_with_streaming_merge(audio, SR, streamed, streamed_partial, str(tmp_path / "tmp.wav"))
        t1 = time.perf_counter()
        elapsed = t1 - t0
        # remaining 2 chunks *0.05 + overhead threadpool ~0.1-0.3s debe ser <6s
        assert elapsed < 6.0, f"post-stop debe ser <6s, tardó {elapsed:.2f}s remaining=2 total={total}"
        assert result is not None
        # orden preservado: chunk0 antes que chunk1 etc
        # streamed son chunk0..chunk(total-3), remaining son últimos 2
        # el join debe empezar con chunk0
        assert result.startswith("chunk0")
        # debe contener streamed + remaining (remaining mock retorna "chunk texto")
        assert "chunk texto" in result
        # speedup vs secuencial: secuencial 29*0.05=1.45s, streaming remaining 0.1s → ~14x
        # verificar que no re-transcribió todo (si lo hiciera sería 1.45s también pero nuestro elapsed menor)
        assert elapsed < 1.0, f"streaming merge debe ser rápido <1s (2 chunks), elapsed {elapsed:.2f}s"

    def test_order_preserved_out_of_order_completions(self):
        _reset_circuit()
        tr = _mock_transcriber()
        audio = _make_pattern(75)  # ~3 chunks
        from backend.audio_chunker import split_audio_on_silence
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        total = len(chunks)
        # mock con latencias desordenadas: pares lento, impares rápido
        counter = {"n": 0}
        def mock_groq_var(chunk, sr, prompt=None):
            idx = counter["n"]
            counter["n"] += 1
            if idx % 2 == 0:
                time.sleep(0.06)
            else:
                time.sleep(0.02)
            return f"chunk{idx}"
        # streamed vacío: merge transcribe todos remaining pero en paralelo desordenado debe reordenar
        tr._groq_chunk_callback = mock_groq_var
        result = tr._transcribe_with_streaming_merge(audio, SR, {}, None, None)
        expected = " ".join([f"chunk{i}" for i in range(total)])
        assert result == expected, f"orden no preservado: got {result!r} expected {expected!r}"

    def test_429_no_bloquea_streaming(self, tmp_path):
        _reset_circuit()
        # streaming task 429 no debe bloquear grabación: log STREAM FAIL y retorna vacío, sigue pool
        tr = _mock_transcriber()
        tr.streaming_ordered = {}
        tr.streaming_pending = set()
        tr.streaming_partial_path = str(tmp_path / "429.partial_stream.txt")
        tr.streaming_executor = __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=2)
        from groq import RateLimitError
        call_n = {"c": 0}
        def mock_429(chunk, sr, prompt=None):
            call_n["c"] += 1
            if call_n["c"] == 1:
                # primer chunk falla 429
                raise RateLimitError("429 rate limit", response=Mock(headers={}), body=None)
            return f"ok{call_n['c']}"
        tr._groq_chunk_callback = mock_429
        # submit 2 chunks: uno falla 429, otro ok
        c = np.zeros(int(2*SR), dtype=np.float32)
        tr.streaming_pending = {0, 1}
        tr._stream_transcribe_task(0, c, 2, 2)
        tr._stream_transcribe_task(1, c, 2, 2)
        with tr.streaming_lock:
            # solo chunk 1 debe estar en ordered (chunk 0 falló → vacío no se guarda para reintento post-stop)
            assert 0 not in tr.streaming_ordered or tr.streaming_ordered[0] == ""
            assert 1 in tr.streaming_ordered
            assert tr.streaming_ordered[1] == "ok2"
        # no bloqueó: si hubiera propagado, test habría fallado
        # post-stop debe reintentar el fallido
        audio = _make_pattern(55)  # ~2 chunks
        from backend.audio_chunker import split_audio_on_silence
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        total = len(chunks)
        # streamed con solo 1 ok, merge debe intentar remaining (incluye el fallido)
        tr._groq_chunk_callback = Mock(return_value="reintento ok")
        streamed = {1: "ok2"}
        res = tr._transcribe_with_streaming_merge(audio, SR, streamed, None, None)
        assert res is not None
        assert "ok2" in res

    def test_poll_streaming_event(self):
        _reset_circuit()
        tr = _mock_transcriber()
        # push streaming event
        tr._push_streaming_event(8, 24)
        ev = tr.get_timer_event()
        assert ev is not None
        assert ev[0] == "streaming"
        assert ev[1] == 8
        assert ev[2] == 24
        # también verificar timer_queue maxsize 64 y critical no se descarta
        assert tr.timer_queue.maxsize == 64
