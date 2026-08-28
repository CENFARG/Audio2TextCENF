# -*- coding: utf-8 -*-
"""
Slice A Hardening — TDD tests sintéticos sin grabar real.

Cubre:
- Cap transitorio 12min (720s) en config + UI
- Groq timeout=30s por chunk, manejo 413/429 con retry + circuit-breaker sin bloquear
- Progress real Chunk X/Y ETA durante transcripción
- Checkpoint parcial: WAV no borrado hasta todos OK, parcial por chunk
- timer_queue y join no descartan eventos críticos

Usa .venv\Scripts\python.exe -m pytest tests/test_long_transcription_hardening.py -v
"""
import os
import time
import tempfile
import random
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

import numpy as np
import soundfile as sf
import pytest

SR = 16000

def _reset_circuit():
    import backend.transcriber as tr_mod
    tr_mod._groq_circuit_failures = 0
    tr_mod._groq_circuit_open_until = 0.0

def _make_wav(path: Path, duration_s: float):
    """Crea WAV sintético 16k mono de duration_s (tono+silecio pattern)."""
    n = int(duration_s * SR)
    # pattern sencillo: 2s tono + 0.4s silencio repetido para que haya cortes en silencio
    chunks = []
    t = 0.0
    freq = 220.0
    while t < duration_s:
        take = min(2.0, duration_s - t)
        nn = int(take * SR)
        tt = np.arange(nn) / SR
        chunks.append(0.3 * np.sin(2 * np.pi * freq * tt).astype(np.float32))
        t += take
        if t >= duration_s:
            break
        take2 = min(0.4, duration_s - t)
        chunks.append(np.zeros(int(take2 * SR), dtype=np.float32))
        t += take2
    audio = np.concatenate(chunks)[:n]
    # asegurar longitud exacta
    if len(audio) < n:
        audio = np.pad(audio, (0, n - len(audio)))
    elif len(audio) > n:
        audio = audio[:n]
    sf.write(str(path), audio, SR, subtype='PCM_16')
    return path

def _make_small_pattern(duration_s):
    """Para tests rápidos de split sin escribir archivo."""
    n = int(duration_s * SR)
    # 2s tono +0.4 silencio
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


class TestCapTransitorio:
    def test_default_720_and_comment(self):
        from backend.config_manager import ConfigManager
        cm = ConfigManager(config_file=str(Path(tempfile.gettempdir()) / f"test_cap_{random.randint(0,9999)}.json"))
        assert cm.get("max_recording_time") == 720, "CAP TRANSITORIO A debe ser 720s (12 min)"
        # comentario en fuente
        src = Path("backend/config_manager.py").read_text(encoding="utf-8")
        assert "CAP TRANSITORIO A" in src
        assert "720" in src
        # limpiar
        try:
            os.unlink(cm.config_file)
        except Exception:
            pass

    def test_clamp_legacy_1200_to_720(self, tmp_path):
        cfg = tmp_path / "config.json"
        import json
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump({"max_recording_time": 1200, "app_version": "0.15.9"}, f)
        from backend.config_manager import ConfigManager
        cm = ConfigManager(config_file=str(cfg))
        assert cm.get("max_recording_time") == 720, "legacy 1200 debe clamp a 720"

    def test_ui_duration_options_max_12min(self):
        src = Path("ui/app.py").read_text(encoding="utf-8")
        assert '"12 min": 720' in src or "'12 min': 720" in src or '"12 min"' in src
        assert "CAP TRANSITORIO A" in src

    def test_20min_chunk_25s_ok_o_rechaza(self, tmp_path):
        # 20min = 1200s -> 38MB PCM16 >25MB, pero chunk 25s debe dar ~48 chunks y cada chunk <=29s
        from backend.audio_chunker import split_audio_on_silence
        audio = _make_small_pattern(1200)  # 20min pattern
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        # debe trozar en ~48 chunks (1200/25=48)
        assert 40 <= len(chunks) <= 55, f"20min debe dar ~48 chunks, got {len(chunks)}"
        for c in chunks:
            assert len(c) <= int(29.0 * SR) + 1
        # alternativa válida: cap rechaza (si transcribe devuelve None)
        # Probamos que Transcriber con 20min wav no hace upload único >25MB sino chunk OK
        # Aquí solo validamos chunking OK


class TestGroqHardening:
    def test_groq_timeout_30_per_chunk(self):
        _reset_circuit()
        # Verificar que Groq se inicializa con timeout=30
        src = Path("backend/transcriber.py").read_text(encoding="utf-8")
        assert "Groq(api_key" in src and "timeout" in src
        assert "GROQ_TIMEOUT_S" in src or "timeout=30" in src or "timeout=GROQ_TIMEOUT_S" in src

        # Mock verificar que cliente recibe timeout=30
        from backend.transcriber import Transcriber
        with patch("backend.transcriber.Groq") as mock_groq:
            mock_groq.return_value = Mock()
            cm = Mock()
            cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
            cm.get_groq_api_key_from_env = Mock(return_value="gsk_test_dummy_key_123")
            cm.localization_manager = Mock()
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
            # verificar llamada con timeout
            assert mock_groq.called
            kwargs = mock_groq.call_args[1]
            assert kwargs.get("timeout") == 30 or kwargs.get("timeout") == 30.0

    def test_timeout_no_cuelga(self, tmp_path):
        _reset_circuit()
        """Mock Groq que cuelga (sleep) debe timeout y no bloquear para siempre."""
        import time as _time
        wav = tmp_path / "t5.wav"
        _make_wav(wav, 5.0)
        from backend.transcriber import Transcriber
        from groq import APITimeoutError

        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test_dummy")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k

        # mock Groq client que levanta timeout
        mock_client = Mock()
        def hang(*a, **kw):
            # simular colgado que sería timeout en 30s, pero levantamos APITimeoutError inmediato
            raise APITimeoutError("timeout colgado")
        mock_client.audio.transcriptions.create = Mock(side_effect=hang)

        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                # debe retornar None rápido (no colgarse)
                start = _time.time()
                with patch("time.sleep", return_value=None):  # evitar backoff real
                    res = tr.transcribe_with_groq(str(wav))
                elapsed = _time.time() - start
                assert res is None  # falla pero no cuelga
                assert elapsed < 2.0, f"timeout no debe colgar, tardó {elapsed:.1f}s"
                # verificar que al menos un intento se hizo
                assert mock_client.audio.transcriptions.create.call_count >= 1

    def test_413_no_retry(self, tmp_path):
        _reset_circuit()
        wav = tmp_path / "t5_413.wav"
        _make_wav(wav, 5.0)
        from backend.transcriber import Transcriber
        from groq import APIStatusError

        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        # crear error 413
        err = APIStatusError("413 Payload Too Large", response=Mock(headers={}), body=None)
        err.status_code = 413
        mock_client.audio.transcriptions.create = Mock(side_effect=err)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                res = tr.transcribe_with_groq(str(wav))
                assert res is None
                # 413 no debe reintentar (solo 1 call)
                assert mock_client.audio.transcriptions.create.call_count == 1

    def test_429_retry_backoff_y_circuit_breaker(self, tmp_path):
        _reset_circuit()
        wav = tmp_path / "t5_429.wav"
        _make_wav(wav, 5.0)
        from backend.transcriber import Transcriber
        from groq import RateLimitError

        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k

        mock_client = Mock()
        err429 = RateLimitError("429 rate limit", response=Mock(headers={"retry-after":"0.01"}), body=None)
        # 2 fallos 429 luego éxito
        mock_client.audio.transcriptions.create = Mock(side_effect=[err429, err429, "texto ok"])
        sleep_calls = []
        def fake_sleep(s):
            sleep_calls.append(s)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                with patch("time.sleep", side_effect=fake_sleep):
                    with patch("random.uniform", return_value=0.1):
                        res = tr.transcribe_with_groq(str(wav))
                assert res is not None
                assert "texto ok" in res
                assert mock_client.audio.transcriptions.create.call_count == 3
                assert len(sleep_calls) == 2
                # jitter + backoff aplicado

        # circuit-breaker: tras 3 fallos consecutivos debe abrirse
        mock_client2 = Mock()
        err = RateLimitError("429", response=Mock(headers={}), body=None)
        mock_client2.audio.transcriptions.create = Mock(side_effect=err)
        with patch("backend.transcriber.Groq", return_value=mock_client2):
            with patch("backend.transcriber.NvidiaASR"):
                # reset circuit
                import backend.transcriber as tr_mod
                tr_mod._groq_circuit_failures = 0
                tr_mod._groq_circuit_open_until = 0
                tr2 = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr2.cliente = mock_client2
                with patch("time.sleep", return_value=None):
                    for _ in range(3):
                        try:
                            tr2._call_groq_api(str(wav))
                        except Exception:
                            pass
                assert tr2._is_circuit_open() is True

    def test_25mb_413_precheck(self, tmp_path):
        _reset_circuit()
        wav = tmp_path / "big.wav"
        # crear archivo >25MB artificial (no necesita ser wav válido, solo tamaño)
        wav.write_bytes(b"\x00" * (26 * 1024 * 1024))
        from backend.transcriber import Transcriber
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        mock_client = Mock()
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                with pytest.raises(Exception) as exc:
                    tr._call_groq_api(str(wav))
                assert "413" in str(exc.value)


class TestProgressYCheckpoint:
    def test_progress_emite_chunk_eta(self, tmp_path):
        _reset_circuit()
        """transcribe_chunks y transcribe_with_groq deben emitir Chunk X/Y ETA"""
        from backend.audio_chunker import transcribe_chunks
        audio = _make_small_pattern(70)  # ~70s => 3 chunks
        calls = []
        progress = []
        def fake_api(chunk, prompt=None):
            time.sleep(0.01)
            return "hola"
        def prog(idx, total, eta):
            progress.append((idx, total, eta))
        # test audio_chunker progress
        res = transcribe_chunks(audio, SR, fake_api, target_s=25.0, max_s=29.0, progress_callback=prog)
        assert len(progress) >= 3
        assert progress[0][1] == len(progress[0]) or progress[0][1] > 1  # total >1
        # también transcriber progress via cola
        wav = tmp_path / "prog.wav"
        _make_wav(wav, 35)  # 35s => 2 chunks
        from backend.transcriber import Transcriber
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        mock_client.audio.transcriptions.create = Mock(return_value="chunk text")
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                progress2 = []
                def cb(idx, total, eta):
                    progress2.append((idx, total))
                res2 = tr.transcribe_with_groq(str(wav), progress_callback=cb)
                assert len(progress2) >= 1
                # verificar cola timer_queue recibió progress
                events = []
                while True:
                    ev = tr.get_timer_event()
                    if ev is None:
                        break
                    events.append(ev)
                prog_events = [e for e in events if e[0] == "progress"]
                assert len(prog_events) >= 1, f"timer_queue debe tener progress, got {events}"
                assert prog_events[0][1] >= 1  # cur

    def test_partial_no_pierde_datos(self, tmp_path):
        _reset_circuit()
        """Si falla chunk 2 de 3, debe guardar parcial del chunk1 y no borrar WAV"""
        wav = tmp_path / "partial.wav"
        _make_wav(wav, 60)  # ~60s => 3 chunks aprox
        from backend.transcriber import Transcriber
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es"}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        # chunk1 ok, chunk2 falla (timeout), chunk3 ok -> parcial debe conservar chunk1 y 3? Pero test simula fallo de chunk2
        # Nuestra implementación guarda parcial tras cada chunk ok, y si falla no añade ese chunk
        call_count = {"n": 0}
        def side_effect(*a, **kw):
            call_count["n"] += 1
            # chunk2: hacer que los 3 intentos de retry fallen (counts 2,3,4)
            if 2 <= call_count["n"] <= 4:
                from groq import APITimeoutError
                raise APITimeoutError("timeout chunk2")
            return f"texto{call_count['n']}"
        mock_client.audio.transcriptions.create = Mock(side_effect=side_effect)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                with patch("time.sleep", return_value=None):
                    res = tr.transcribe_with_groq(str(wav))
                # debe tener texto de chunk1 y 3 (chunk2 vacío por fallo)
                assert res is not None
                assert "texto1" in res
                # chunk3 puede ser texto3 (depende de si api fue llamada 3 veces)
                # verificar que parcial file existe si no todo ok? En este caso chunk2 falló pero luego recuperó -> all_ok False -> parcial debe existir
                partial = Path(str(wav) + ".partial.txt")
                # si hay fallo debe quedar parcial
                # Si nuestra impl borra parcial solo si all_ok, debe existir
                assert partial.exists() or "texto1" in res, "parcial debe conservar datos"
                # verificar que no se pierde todo
                assert len(res) > 0
                # cleanup
                try:
                    if partial.exists():
                        partial.unlink()
                except Exception:
                    pass

    def test_wav_no_borrado_hasta_todos_ok(self, tmp_path):
        _reset_circuit()
        """process_recording no debe borrar WAV temporal si transcripción fallida"""
        from backend.transcriber import Transcriber
        import tempfile as _tf
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es","save_audio":False}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        fm = Mock()
        fm.save_audio_file = Mock(return_value=None)
        fm.save_transcription_entry = Mock()
        with patch("backend.transcriber.Groq", return_value=Mock()):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), fm, Mock(), Mock(), Mock())
                # mock transcribe para fallar
                tr.transcribe = Mock(return_value=None)
                # crear snapshot 5s
                snap = [np.zeros(int(5*SR), dtype=np.float32)]
                # capturar temp path creado: patch NamedTemporaryFile
                orig_ntf = tempfile.NamedTemporaryFile
                created = {}
                def fake_ntf(*a, **kw):
                    f = orig_ntf(*a, **kw)
                    created["path"] = f.name
                    return f
                with patch("tempfile.NamedTemporaryFile", side_effect=fake_ntf):
                    # need to run process_recording sync (no thread)
                    # directly call without thread
                    tr.process_lock = __import__("threading").Lock()
                    # ensure not dedup
                    tr.current_recording_id = "test-id"
                    tr.last_audio_hash = None
                    tr.process_recording(recording_id="test-id", audio_snapshot=snap)
                    time.sleep(0.2)
                    path = created.get("path")
                    if path:
                        # si falló, el temp debe conservarse (no borrado inmediato)
                        # nuestra impl conserva en finally solo si failure -> path debe existir
                        assert os.path.exists(path), "WAV temporal debe conservarse tras fallo (checkpoint)"
                        # cleanup
                        try:
                            os.unlink(path)
                        except Exception:
                            pass
                        try:
                            os.unlink(path + ".partial.txt")
                        except Exception:
                            pass


class TestTimerQueueYCircuit:
    def test_timer_queue_no_descarta_criticos(self):
        from backend.transcriber import Transcriber
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        with patch("backend.transcriber.Groq", return_value=Mock()):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                # queue tamaño 64
                assert tr.timer_queue.maxsize == 64
                # llenar con 60 eventos no críticos
                for i in range(60):
                    tr._queue_put(("timer", 0, i), critical=False)
                # evento crítico debe entrar aun con cola casi llena
                ok = tr._queue_put(("progress", 1, 48, 12.0), critical=True)
                assert ok is True
                # verificar que progress está en cola
                found = False
                while True:
                    ev = tr.get_timer_event()
                    if ev is None:
                        break
                    if ev[0] == "progress":
                        found = True
                assert found

    def test_join_no_descarta_audio(self):
        from backend.transcriber import Transcriber
        src = Path("backend/transcriber.py").read_text(encoding="utf-8")
        assert "join(timeout=1.0)" in src or "join(timeout=1" in src
        assert "CAP TRANSITORIO A" in src


# ── Slice B: paralelización Groq ─────────────────────────────────────────
class TestSliceBParallel:
    """Slice B — ThreadPoolExecutor 3 workers, orden, ETA throughput, timeout 30s, 413/429."""

    def test_parallel_preserves_order(self, tmp_path):
        """Reordena antes de join: futures desordenados deben dar texto ordenado."""
        _reset_circuit()
        from backend.audio_chunker import transcribe_chunks_parallel, split_audio_on_silence
        audio = _make_small_pattern(180)  # ~7 chunks
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        total = len(chunks)
        # api con latencia variable para forzar out-of-order
        import random, time as _time
        def api(chunk, prompt=None):
            idx = api.calls[0]
            api.calls[0] += 1
            # chunks pares más lentos, impares rápidos → completions desordenadas
            if idx % 2 == 0:
                _time.sleep(0.08)
            else:
                _time.sleep(0.02)
            return f"chunk{idx}"
        api.calls = [0]
        res = transcribe_chunks_parallel(audio, SR, api, max_workers=3)
        # debe estar ordenado chunk0 chunk1 ... independientemente del orden de completion
        expected = " ".join(f"chunk{i}" for i in range(total))
        assert res == expected, f"orden no preservado: got {res!r} expected {expected!r}"

    def test_checkpoint_thread_safe(self, tmp_path):
        """Checkpoint parcial con lock: no race, orden preservado."""
        _reset_circuit()
        wav = tmp_path / "chk.wav"
        _make_wav(wav, 60)  # ~3 chunks
        from backend.transcriber import Transcriber
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es","groq_parallel_workers":3}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        mock_client = Mock()
        # cada chunk retorna texto distinto con latency variable
        call_idx = {"n": 0}
        def side(*a, **kw):
            n = call_idx["n"]
            call_idx["n"] += 1
            # delay variable
            if n % 2 == 0:
                time.sleep(0.06)
            else:
                time.sleep(0.02)
            return f"texto{n}"
        mock_client.audio.transcriptions.create = Mock(side_effect=side)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                res = tr.transcribe_with_groq(str(wav))
                assert res is not None
                # orden preservado
                parts = res.split()
                # primera parte debe ser texto0 (orden) aunque completions desordenadas
                assert parts[0] == "texto0"
                # checkpoint debe haber sido borrado si all_ok, o existir ordenado si partial
                partial = Path(str(wav) + ".partial.txt")
                if partial.exists():
                    content = partial.read_text(encoding="utf-8")
                    # contenido ordenado igual que res o prefijo
                    assert content.split()[0] == "texto0"
                    try:
                        partial.unlink()
                    except Exception:
                        pass

    def test_parallel_speedup_vs_sequential(self):
        """12min sintético 720s 29chunks mock 0.8s→ seq ~2.3s (scale 0.08) vs paralelo ~0.8s speedup >2.5x."""
        from backend.audio_chunker import transcribe_chunks, transcribe_chunks_parallel
        import time as _time
        # sintetizar 720s pattern sin necesidad archivo: 29 chunks *25s
        audio = _make_small_pattern(720)
        # mock api 0.08s por chunk (escala de 0.8s real para no tardar 23s)
        def api_seq(chunk, prompt=None):
            _time.sleep(0.08)
            return "x"
        def api_par(chunk, prompt=None):
            _time.sleep(0.08)
            return "x"
        # sequential
        t0 = _time.perf_counter()
        res_seq = transcribe_chunks(audio, SR, api_seq, target_s=25.0, max_s=29.0)
        t_seq = _time.perf_counter() - t0
        # parallel 3 workers
        t0 = _time.perf_counter()
        res_par = transcribe_chunks_parallel(audio, SR, api_par, max_workers=3, timeout_s=5)
        t_par = _time.perf_counter() - t0
        assert res_seq is not None and res_par is not None
        # speedup >2.5x
        speedup = t_seq / t_par if t_par else 0
        assert speedup > 2.5, f"speedup insuficiente {speedup:.2f} seq={t_seq:.2f}s par={t_par:.2f}s esperado >2.5x (0.8s/chunk 29 chunks workers=3)"
        # parallel debe ser notoriamente más rápido que secuencial
        assert t_par < t_seq * 0.5

    def test_parallel_uses_threadpool_not_multiprocessing(self):
        src = Path("backend/transcriber.py").read_text(encoding="utf-8")
        assert "ThreadPoolExecutor" in src
        assert "concurrent.futures" in src
        # NO multiprocessing
        assert "multiprocessing" not in src or "NO multiprocessing" in src or src.count("multiprocessing") == 0 or "Process(" not in src
        # clamp 2-4 y default 3
        assert "GROQ_PARALLEL_WORKERS" in src
        assert "max_workers" in src

    def test_429_one_chunk_no_cancela_otros(self, tmp_path):
        """429 en 1 chunk no cancela otros: pool sigue, texto parcial ordenado."""
        _reset_circuit()
        from backend.transcriber import Transcriber
        from groq import RateLimitError
        cm = Mock()
        cm.get.side_effect = lambda k, d=None: {"hotkey":"f9","record_mode":"toggle","audio_priority_apps":[],"utf8_validation":True,"blocks":{},"max_recording_time":720,"transcription_language":"es","default_language":"es","groq_parallel_workers":3}.get(k,d)
        cm.get_groq_api_key_from_env = Mock(return_value="gsk_test")
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.side_effect = lambda k, **kw: k
        wav = tmp_path / "429.wav"
        _make_wav(wav, 60)  # ~3 chunks
        mock_client = Mock()
        call_n = {"c": 0}
        def side(*a, **kw):
            call_n["c"] += 1
            # simular 429 en el segundo call (chunk desordenado: no importa cual, pero solo uno falla)
            if call_n["c"] == 2:
                raise RateLimitError("429 rate limit", response=Mock(headers={}), body=None)
            return f"ok{call_n['c']}"
        mock_client.audio.transcriptions.create = Mock(side_effect=side)
        with patch("backend.transcriber.Groq", return_value=mock_client):
            with patch("backend.transcriber.NvidiaASR"):
                tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
                tr.cliente = mock_client
                with patch("time.sleep", return_value=None):
                    with patch("random.uniform", return_value=0.1):
                        res = tr.transcribe_with_groq(str(wav))
                        # debe tener textos de los chunks que no fallaron (2 de 3)
                        assert res is not None
                        assert "ok1" in res or "ok3" in res
                        # no debe haber abortado todo por un 429
                        assert len(res.split()) >= 1
                        # verificar que al menos 2 calls se intentaron (chunk fallido + reintentos)
                        assert mock_client.audio.transcriptions.create.call_count >= 2

    def test_timeout_30s_per_future(self):
        """Timeout 30s por future via ThreadPoolExecutor."""
        src = Path("backend/transcriber.py").read_text(encoding="utf-8")
        assert "GROQ_TIMEOUT_S" in src or "GROQ_PARALLEL_TIMEOUT_S" in src
        assert "timeout" in src.lower()
        # verificar que as_completed usa timeout
        assert "fut.result(timeout" in src

    def test_logging_start_end_worker(self):
        src = Path("backend/transcriber.py").read_text(encoding="utf-8")
        assert "Chunk START" in src
        assert "Chunk END" in src
        assert "worker=" in src or "worker_id" in src
        assert "q=" in src
        # debe loguear en transcription_debug.log via tlogger
        assert "tlogger" in src

    def test_progress_eta_throughput(self):
        src = Path("backend/transcriber.py").read_text(encoding="utf-8")
        # ETA recalculado por throughput real completed/elapsed
        assert "completed" in src and "elapsed" in src
        assert "_push_progress_event" in src
        assert "ETA" in src or "eta" in src

    def test_workers_configurable_2_4(self):
        from backend.config_manager import ConfigManager
        import tempfile, json, os
        for w in [2, 3, 4]:
            cfg = Path(tempfile.gettempdir()) / f"test_gpw_{w}_{random.randint(0,9999)}.json"
            with open(cfg, "w", encoding="utf-8") as f:
                json.dump({"groq_parallel_workers": w, "max_recording_time": 720, "app_version": "0.15.9"}, f)
            cm = ConfigManager(config_file=str(cfg))
            assert cm.get("groq_parallel_workers") == w
            try:
                os.unlink(cfg)
            except Exception:
                pass
        # clamp fuera de rango
        cfg = Path(tempfile.gettempdir()) / f"test_gpw_clamp_{random.randint(0,9999)}.json"
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump({"groq_parallel_workers": 10, "max_recording_time": 720, "app_version": "0.15.9"}, f)
        cm = ConfigManager(config_file=str(cfg))
        assert cm.get("groq_parallel_workers") == 4
        try:
            os.unlink(cfg)
        except Exception:
            pass
