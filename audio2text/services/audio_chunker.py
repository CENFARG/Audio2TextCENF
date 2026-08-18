"""@File: audio2text/services/audio_chunker.py
@Description: Audio chunking for safe transcription windows (<30s).

WHY (bug v0.15.0 — "tildes que se caen"):
Groq processes long audio by splitting on the server side, and at the
boundaries between windows it loses audio: entire phrases disappear and
words get cut right at the stressed syllable ("grabaci", "ning",
"comunicaci", "está"→"est"). Verified empirically: the SAME WAV
transcribed as a 60s segment comes out perfect, and as a 296s file it
comes out with cuts — same model (whisper-large-v3), temperature=0.

The solution is to chunk on the CLIENT side by cutting at silences:
each window sent contains complete words, the decoder never receives a
split word, and we don't depend on Groq's internal chunking. Groq's own
documentation recommends client-side chunking for long audio.

Invariants (covered by tests):
1. NO sample is lost: concat(chunks) == original audio.
2. No chunk exceeds the hard Whisper window (30s).
3. Cuts fall on silences >=140ms; only if NO silence exists in the
   search range is a hard cut applied.

@Version: 0.16.0
@Author: Audio2Text Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
from typing import Callable, List, Optional

import numpy as np

# Hard Whisper window: NO chunk can exceed 30s of audio.
MAX_WINDOW_S = 30.0

# Defaults: aim for ~25s with a 29s ceiling (safety margin).
DEFAULT_TARGET_S = 25.0
DEFAULT_MAX_S = 29.0

# Audio >= this threshold gets chunked to avoid Groq seam loss.
CHUNK_THRESHOLD_S = 28.0

logger = logging.getLogger(__name__)


def _silence_threshold_db(db: np.ndarray) -> float:
    """Adaptive silence threshold in dB from the audio profile.

    If the audio has speech/silence contrast (percentile 90 vs 10),
    the threshold anchors on the noise floor; if uniform (no clear
    silences), it falls to -45 dBFS and simply won't have candidates.
    """
    lo, hi = np.percentile(db, [10, 90])
    if hi - lo > 12.0:
        thr = lo + 0.25 * (hi - lo)
    else:
        thr = -45.0
    return float(np.clip(thr, -60.0, -25.0))


def _silence_cut_points(
    audio: np.ndarray,
    sr: int,
    frame_ms: float,
    min_silence_ms: float,
) -> List[int]:
    """Centers (in samples) of silence zones >= min_silence_ms."""
    frame = max(1, int(sr * frame_ms / 1000.0))
    n = len(audio) // frame
    if n == 0:
        return []
    frames = audio[: n * frame].reshape(n, frame)
    rms = np.sqrt((frames**2).mean(axis=1))
    db = 20.0 * np.log10(rms + 1e-9)
    silent = db < _silence_threshold_db(db)

    min_frames = max(1, int(round(min_silence_ms / frame_ms)))
    points: list[int] = []
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


def split_audio_on_silence(
    audio: np.ndarray,
    sr: int,
    target_s: float = DEFAULT_TARGET_S,
    max_s: float = DEFAULT_MAX_S,
    min_chunk_s: float = 5.0,
    min_tail_s: float = 1.0,
    frame_ms: float = 20.0,
    min_silence_ms: float = 140.0,
) -> List[np.ndarray]:
    """Split audio into chunks <= max_s by cutting at silences.

    Strategy per chunk: find the silence center closest to the target
    (target_s) within [pos+min_chunk_s, pos+max_s]. If no silence exists
    in that range, hard cut at target_s (caller logs). The final short
    tail is merged with the previous chunk if it fits within the window
    limit.

    Args:
        audio: mono signal as numpy array (float).
        sr: sample rate.
        target_s: target duration per chunk.
        max_s: max duration per chunk (hard ceiling, < Whisper window).
        min_chunk_s: minimum duration of an intermediate chunk.
        min_tail_s: tails shorter than this merge if possible.
        frame_ms: energy analysis resolution.
        min_silence_ms: minimum silence duration to be a cut point.

    Returns:
        List of arrays whose concatenation is EXACTLY the original audio.
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
            # No silence in entire range: hard cut (no alternative).
            cut = pos + target_samples
            logger.warning(
                "No silence found in range [%d, %d], hard cut at %d",
                lo_i,
                hi_i,
                cut,
            )
        bounds.append(cut)
        pos = cut

    chunks = [audio[bounds[i] : bounds[i + 1]] for i in range(len(bounds) - 1)]

    # Short tail: merge with previous chunk if it doesn't break the limit.
    if len(chunks) >= 2 and len(chunks[-1]) < int(min_tail_s * sr):
        if len(chunks[-2]) + len(chunks[-1]) <= max_samples:
            merged = np.concatenate([chunks[-2], chunks[-1]])
            chunks[-2:] = [merged]

    return chunks


def transcribe_chunks(
    audio: np.ndarray,
    sr: int,
    api_call: Callable[[np.ndarray, Optional[str]], str],
    target_s: float = DEFAULT_TARGET_S,
    max_s: float = DEFAULT_MAX_S,
    prompt_chars: int = 300,
    operation_id: Optional[str] = None,
    event_callback: Optional[Callable[[dict], None]] = None,
) -> str:
    """Transcribe long audio by chunking, joining texts from each chunk.

    Chains a `prompt` with the end of the previous text on each call:
    Whisper uses that prompt to maintain style consistency, punctuation,
    and vocabulary between windows (recommended practice from Groq docs
    for chunked transcription).

    Args:
        audio: complete mono signal.
        sr: sample rate.
        api_call: callable(chunk, prompt) -> transcribed text for that chunk.
            `prompt` is None on the first call.
        target_s / max_s: chunking parameters.
        prompt_chars: how many characters of previous context to pass as prompt.

    Returns:
        Joined text from all chunks.
    """
    chunks = split_audio_on_silence(audio, sr, target_s=target_s, max_s=max_s)
    texts: list[str] = []
    for chunk_index, chunk in enumerate(chunks):
        prompt: str | None = None
        if texts:
            joined = " ".join(texts)
            prompt = joined[-prompt_chars:].strip()
        part = api_call(chunk, prompt=prompt)
        if part:
            part = part.strip()
        if part:
            if event_callback:
                event_callback(
                    {
                        "event_type": "chunk_aggregate",
                        "text": part,
                        "chunk_index": chunk_index,
                        "attempt": 1,
                    }
                )
            words = part.split()
            if texts:
                previous = texts[-1].split()
                overlap = max(
                    (
                        n
                        for n in range(1, min(len(previous), len(words)) + 1)
                        if previous[-n:] == words[:n]
                    ),
                    default=0,
                )
                words = words[overlap:]
            if words:
                texts.append(" ".join(words))
    return " ".join(texts)
