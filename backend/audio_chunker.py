# -*- coding: utf-8 -*-
"""
Trozado de audio para transcripción en ventanas seguras (<30s).

WHY (bug v0.15.0 — "tildes que se caen"):
Groq procesa archivos largos partiendo el audio en ventanas del lado
SERVIDOR, y en las costuras entre ventanas pierde audio: frases enteras
desaparecen y las palabras quedan cortadas justo en la sílaba tónica
("grabaci", "ning", "comunicaci", "está"→"est"). Verificado empíricamente:
el MISMO WAV transcrito como segmento de 60s sale perfecto, y como archivo
de 296s sale con cortes — mismo modelo (whisper-large-v3), temperature=0.

La solución es trozar del lado CLIENTE cortando en SILENCIOS: cada ventana
enviada contiene palabras completas, el decoder nunca recibe una palabra
partida, y no dependemos del chunking interno de Groq. La propia
documentación de Groq recomienda chunking del lado cliente para audio largo.

Invariantes (cubiertos por tests/test_audio_chunker.py):
1. NINGÚN sample se pierde: concat(chunks) == audio original.
2. Ningún chunk supera la ventana dura de Whisper (30s).
3. Los cortes caen en silencios ≥140ms; solo si NO hay ningún silencio
   en el rango de búsqueda se aplica un corte duro.

Author: Audio2Text Development Team
Version: 0.15.1
"""

from typing import Callable, List, Optional

import numpy as np

# Ventana dura de Whisper: NINGÚN chunk puede superar 30s de audio.
MAX_WINDOW_S = 30.0

# Defaults: apuntamos a ~25s con techo de 29s (margen de seguridad).
DEFAULT_TARGET_S = 25.0
DEFAULT_MAX_S = 29.0


def _silence_threshold_db(db: np.ndarray) -> float:
    """Umbral adaptativo de silencio en dB a partir del perfil del audio.

    Si el audio tiene contraste habla/silencio (percentil 90 vs 10),
    el umbral se apoya en el piso de ruido; si es uniforme (sin
    silencios claros), cae a -45 dBFS y simplemente no habrá candidatos.
    """
    lo, hi = np.percentile(db, [10, 90])
    if hi - lo > 12.0:
        thr = lo + 0.25 * (hi - lo)
    else:
        thr = -45.0
    return float(np.clip(thr, -60.0, -25.0))


def _silence_cut_points(audio: np.ndarray, sr: int, frame_ms: float,
                        min_silence_ms: float) -> List[int]:
    """Centros (en samples) de las zonas de silencio ≥ min_silence_ms."""
    frame = max(1, int(sr * frame_ms / 1000.0))
    n = len(audio) // frame
    if n == 0:
        return []
    frames = audio[:n * frame].reshape(n, frame)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    db = 20.0 * np.log10(rms + 1e-9)
    silent = db < _silence_threshold_db(db)

    min_frames = max(1, int(round(min_silence_ms / frame_ms)))
    points = []
    i = 0
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            if (j - i) >= min_frames:
                center_frame = (i + j) // 2
                points.append(center_frame * frame)
            i = j
        else:
            i += 1
    return points


def split_audio_on_silence(audio: np.ndarray, sr: int,
                           target_s: float = DEFAULT_TARGET_S,
                           max_s: float = DEFAULT_MAX_S,
                           min_chunk_s: float = 5.0,
                           min_tail_s: float = 1.0,
                           frame_ms: float = 20.0,
                           min_silence_ms: float = 140.0) -> List[np.ndarray]:
    """Trozar audio en chunks ≤ max_s cortando en silencios.

    Estrategia por chunk: buscar el centro de silencio más cercano al
    objetivo (target_s) dentro de [pos+min_chunk_s, pos+max_s]. Si no hay
    ningún silencio en ese rango, corte duro en target_s (logging del
    llamador). La cola final corta se fusiona con el chunk anterior si
    cabe dentro del límite de ventana.

    Args:
        audio: señal mono como array numpy (float).
        sr: sample rate.
        target_s: duración objetivo por chunk.
        max_s: duración máxima por chunk (techo duro, < ventana Whisper).
        min_chunk_s: duración mínima de un chunk intermedio.
        min_tail_s: las colas más cortas que esto se fusionan si es posible.
        frame_ms: resolución del análisis de energía.
        min_silence_ms: duración mínima de silencio para ser punto de corte.

    Returns:
        Lista de arrays cuya concatenación es EXACTAMENTE el audio original.
    """
    audio = np.asarray(audio)
    total = len(audio)
    max_samples = int(max_s * sr)
    if total <= max_samples:
        return [audio]

    target_samples = int(target_s * sr)
    min_chunk_samples = int(min_chunk_s * sr)
    points = _silence_cut_points(audio, sr, frame_ms, min_silence_ms)

    bounds = [0]
    pos = 0
    while True:
        remaining = total - pos
        if remaining <= max_samples:
            bounds.append(total)
            break
        lo_i = pos + min_chunk_samples
        hi_i = pos + max_samples
        candidates = [c for c in points if lo_i <= c <= hi_i]
        if candidates:
            ideal = pos + target_samples
            cut = min(candidates, key=lambda c: abs(c - ideal))
        else:
            # Sin silencio en todo el rango: corte duro (no hay alternativa).
            cut = pos + target_samples
        bounds.append(cut)
        pos = cut

    chunks = [audio[bounds[i]:bounds[i + 1]] for i in range(len(bounds) - 1)]

    # Cola corta: fusionarla con el chunk anterior si no rompe el límite.
    if len(chunks) >= 2 and len(chunks[-1]) < int(min_tail_s * sr):
        if len(chunks[-2]) + len(chunks[-1]) <= max_samples:
            merged = np.concatenate([chunks[-2], chunks[-1]])
            chunks[-2:] = [merged]

    return chunks


def transcribe_chunks(audio: np.ndarray, sr: int,
                      api_call: Callable[[np.ndarray, Optional[str]], str],
                      target_s: float = DEFAULT_TARGET_S,
                      max_s: float = DEFAULT_MAX_S,
                      prompt_chars: int = 300) -> str:
    """Transcribir audio largo troceado, uniendo los textos de cada chunk.

    Encadena un `prompt` con el final del texto anterior en cada llamada:
    Whisper usa ese prompt para mantener consistencia de estilo, puntuación
    y vocabulario entre ventanas (práctica recomendada por la doc de Groq
    para transcripción por chunks).

    Args:
        audio: señal mono completa.
        sr: sample rate.
        api_call: callable(chunk, prompt) -> texto transcrito de ese chunk.
            `prompt` es None en la primera llamada.
        target_s / max_s: parámetros del trozado.
        prompt_chars: cuántos caracteres de contexto previo pasar como prompt.

    Returns:
        Texto unido de todos los chunks.
    """
    chunks = split_audio_on_silence(audio, sr, target_s=target_s, max_s=max_s)
    texts = []
    for chunk in chunks:
        prompt = None
        if texts:
            joined = " ".join(texts)
            prompt = joined[-prompt_chars:].strip()
        part = api_call(chunk, prompt=prompt)
        if part:
            part = part.strip()
        if part:
            texts.append(part)
    return " ".join(texts)
