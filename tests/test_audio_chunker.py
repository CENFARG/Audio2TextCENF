# -*- coding: utf-8 -*-
"""
Tests del trozador de audio para transcripción en ventanas <30s.

Contexto (bug v0.15.0): Groq procesa audio largo en ventanas del lado
servidor y en las costuras pierde frases enteras y palabras ("tildes que
se caen": grabaci, ning, comunicaci). La solución es trozar del lado
cliente cortando en SILENCIOS, para que cada ventana contenga palabras
completas.

Invariantes críticos:
1. NINGÚN sample se pierde: concat(chunks) == audio original.
2. Ningún chunk supera la ventana dura de Whisper (30s).
3. Los cortes caen en silencios (nunca a mitad de palabra), salvo
   corte duro excepcional cuando no hay silencio en todo el rango.
"""

import numpy as np
import pytest

from backend.audio_chunker import (
    MAX_WINDOW_S,
    split_audio_on_silence,
    transcribe_chunks,
)

SR = 16000


def make_speech_silence_pattern(total_s, speech_s=2.0, silence_s=0.4, freq=220.0, sr=SR):
    """Audio sintético: bloques de tono (habla) separados por silencio real (zeros)."""
    chunks = []
    t = 0.0
    while t < total_s:
        take_s = min(speech_s, total_s - t)
        n = int(take_s * sr)
        tt = np.arange(n) / sr
        chunks.append(0.3 * np.sin(2 * np.pi * freq * tt))
        t += take_s
        if t >= total_s:
            break
        take_s = min(silence_s, total_s - t)
        chunks.append(np.zeros(int(take_s * sr)))
        t += take_s
    return np.concatenate(chunks)


class TestSplitAudioOnSilence:
    def test_audio_corto_un_solo_chunk(self):
        audio = make_speech_silence_pattern(10.0)
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        assert len(chunks) == 1
        assert len(chunks[0]) == len(audio)

    def test_ningun_sample_se_pierde(self):
        rng = np.random.default_rng(42)
        audio = rng.standard_normal(int(100 * SR)) * 0.1
        chunks = split_audio_on_silence(audio, SR)
        assert sum(len(c) for c in chunks) == len(audio)

    def test_chunks_dentro_del_limite_de_ventana(self):
        audio = make_speech_silence_pattern(120.0)
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= int(29.0 * SR) + 1, "chunk supera la ventana de 30s de Whisper"

    def test_cortes_caen_en_silencios(self):
        # patrón 2s tono + 0.4s silencio; target 6.5s → el corte debe caer
        # dentro de una zona de silencio (RMS ~0 en el borde)
        audio = make_speech_silence_pattern(60.0)
        chunks = split_audio_on_silence(audio, SR, target_s=6.5, max_s=8.0)
        assert len(chunks) > 2
        for c in chunks[:-1]:
            edge = c[-int(0.05 * SR):]  # últimos 50ms del chunk
            assert np.sqrt((edge ** 2).mean()) < 1e-3, "corte cayó dentro de habla"

    def test_tono_continuo_corte_duro_sin_perder_audio(self):
        # sin silencios: corte duro, pero se respetan límites y no hay pérdida
        t = np.arange(int(65 * SR)) / SR
        audio = 0.3 * np.sin(2 * np.pi * 220 * t)
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0)
        assert len(chunks) >= 3
        assert sum(len(c) for c in chunks) == len(audio)
        for c in chunks:
            assert len(c) <= int(29.0 * SR) + 1

    def test_cola_corta_se_fusiona_con_el_anterior(self):
        # 26.5s con silencio al final: la cola de 1.5s no debe quedar sola
        audio = make_speech_silence_pattern(26.5)
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0, min_tail_s=2.0)
        assert len(chunks) == 1
        assert len(chunks[0]) == len(audio)

    def test_no_crea_chunks_absurdamente_chicos(self):
        audio = make_speech_silence_pattern(90.0)
        chunks = split_audio_on_silence(audio, SR, target_s=25.0, max_s=29.0, min_chunk_s=5.0)
        for c in chunks[:-1]:
            assert len(c) >= int(5.0 * SR) - 1
        # el último puede ser más corto (cola), pero > 0
        assert len(chunks[-1]) > 0


class TestTranscribeChunks:
    def test_una_llamada_por_chunk_y_texto_unido(self):
        audio = make_speech_silence_pattern(70.0)
        calls = []

        def fake_api(chunk_bytes_or_path, prompt=None):
            calls.append(len(chunk_bytes_or_path) if hasattr(chunk_bytes_or_path, "__len__") else 0)
            return f"texto{len(calls)}"

        result = transcribe_chunks(audio, SR, fake_api, target_s=25.0, max_s=29.0)
        assert len(calls) >= 2
        assert result == " ".join(f"texto{i+1}" for i in range(len(calls)))

    def test_audio_corto_una_sola_llamada(self):
        audio = make_speech_silence_pattern(12.0)
        calls = []

        def fake_api(chunk, prompt=None):
            calls.append(1)
            return "hola"

        result = transcribe_chunks(audio, SR, fake_api)
        assert len(calls) == 1
        assert result == "hola"

    def test_prompt_encadena_texto_previo(self):
        audio = make_speech_silence_pattern(70.0)
        prompts = []

        def fake_api(chunk, prompt=None):
            prompts.append(prompt)
            return f"parte{len(prompts)}"

        transcribe_chunks(audio, SR, fake_api, target_s=25.0, max_s=29.0)
        assert prompts[0] is None
        # desde la segunda llamada, el prompt contiene el texto anterior
        for i, p in enumerate(prompts[1:], start=1):
            assert p and f"parte{i}" in p
