"""
Double-transcription reproduction tests (bug-fix batch 2, item B4).

User report (Pablo): "under some condition the transcription returns
doubled, pasted twice back to back."

ROOT CAUSE (deterministic, streaming merge path — Slice C):

``_stream_snapshot_and_submit`` re-splits the audio recorded SO FAR every
25s. When the buffer is <= max_s (29s) the chunker returns ONE single chunk
covering the whole buffer, and the old code submitted it immediately (the
``total == 1`` exception in the tail-exclusion rule). A whole-buffer chunk
is a TAIL chunk: its end boundary is not stable yet. The post-stop split of
the FULL audio re-cuts that region at the silence nearest the 25s target,
which can fall BEFORE the snapshot buffer end.

``_transcribe_with_streaming_merge`` trusts index correlation
(``remaining = indices not in streamed_ordered``), so it transcribes the
final chunks that start before the streamed chunk's real audio end — the
same audio region is transcribed TWICE (once inside the streamed text, once
in the merge text). The doubled text is displayed and auto-pasted twice
back to back.

Deterministic repro with silences at ~23.24s and ~45.24s:

- 25s snapshot: single chunk [0, 25] → old code streams it immediately.
- Full 63s audio: cuts at ~23.24 and ~45.24 → 3 chunks.
- Merged intervals: [0, 25] (streamed) + [23.24, 45.24] + [45.24, 63]
  → region [23.24, 25] transcribed twice.

FIX (fail closed, same rule as every other tail): never submit the tail
chunk of a snapshot while recording — its end boundary is not final.
Each transcribed marker below carries the TRUE audio interval of its chunk,
so overlap in the merged text is measured directly on audio time.
"""

import concurrent.futures
import re
from unittest.mock import Mock, patch

import numpy as np

from backend.audio_chunker import split_audio_on_silence

SR = 16000
SILENCE_CENTERS_S = (23.24, 45.24)  # ~centers of the 500ms silence zones
INTERVAL_RE = re.compile(r"\[(\d+\.?\d*)-(\d+\.?\d*)\]")


def _reset_circuit():
    import backend.transcriber as tr_mod

    tr_mod._groq_circuit_failures = 0
    tr_mod._groq_circuit_open_until = 0.0


def _make_marked_audio(duration_s: float) -> np.ndarray:
    """Audio with known silence zones and per-second level markers.

    Seconds of speech are constant non-zero levels (unique per second so a
    chunk's content identifies its position); 500ms silence zones sit at
    23.0-23.5s and 45.0-45.5s so the chunker cuts near 23.24s / 45.24s.
    """
    n = int(duration_s * SR)
    audio = np.ones(n, dtype=np.float32)
    sec = np.arange(n) // SR
    audio[:] = ((sec % 50) + 1).astype(np.float32)
    for center_start in (23.0, 45.0):
        a = int(center_start * SR)
        b = int((center_start + 0.5) * SR)
        audio[a:b] = 0.0
    return audio


def _interval_map(chunks, starts, ends):
    """Map rounded chunk duration (s) -> true (start, end) audio interval."""
    mapping = {}
    for chunk, start, end in zip(chunks, starts, ends, strict=True):
        mapping[round(len(chunk) / SR, 3)] = (float(start), float(end))
    return mapping


def _mock_transcriber(tmp_path):
    from backend.transcriber import Transcriber

    cm = Mock()
    cm.get.side_effect = lambda k, d=None: {
        "hotkey": "f9",
        "record_mode": "toggle",
        "audio_priority_apps": [],
        "utf8_validation": False,
        "blocks": {},
        "max_recording_time": 720,
        "transcription_language": "es",
        "default_language": "es",
        "groq_parallel_workers": 3,
        "save_audio": False,
    }.get(k, d)
    cm.get_groq_api_key_from_env = Mock(return_value="gsk_test_dummy_key_123")
    cm.localization_manager = Mock()
    cm.localization_manager.get_string.side_effect = lambda k, **kw: k
    with patch("backend.transcriber.Groq", return_value=Mock()), patch(
        "backend.transcriber.NvidiaASR"
    ), patch("backend.transcriber.sd.InputStream", Mock()), patch(
        "backend.transcriber.keyboard", Mock()
    ), patch(
        "backend.transcriber.psutil.process_iter", return_value=[]
    ):
        tr = Transcriber(cm, Mock(), Mock(), Mock(), Mock(), Mock())
        tr.ejecutando = False
    # Hermetic: no vocab corrections on marker texts
    tr.custom_vocab = Mock()
    tr.custom_vocab.apply_corrections = Mock(side_effect=lambda t: t)
    return tr


def _parse_intervals(text):
    return sorted((float(a), float(b)) for a, b in INTERVAL_RE.findall(text))


def _assert_no_overlap(intervals):
    for (s1, e1), (s2, e2) in zip(intervals, intervals[1:], strict=False):
        assert s2 >= e1 - 0.01, (
            f"doubled audio region: [{s1:.2f}, {e1:.2f}] overlaps "
            f"[{s2:.2f}, {e2:.2f}] — transcription contains duplicated audio"
        )


class TestStreamingMergeDoubling:
    """B4: the whole-buffer first snapshot must never be streamed."""

    def test_first_snapshot_tail_not_streamed_no_doubling(self, tmp_path):
        """End-to-end repro: 25s snapshot + 63s recording must not double.

        RED (pre-fix): the 25s single-chunk snapshot IS submitted, and the
        merge re-transcribes final chunks starting at 23.24s → region
        [23.24, 25] appears in two markers → doubled transcription.
        GREEN (post-fix): the tail chunk is never streamed while recording,
        streamed_ordered stays empty for this recording, and the merge
        transcribes every final chunk exactly once.
        """
        _reset_circuit()
        tr = _mock_transcriber(tmp_path)

        full = _make_marked_audio(63.0)
        snapshot_audio = full[: int(25.0 * SR)]

        final_chunks = split_audio_on_silence(full, SR, target_s=25.0, max_s=29.0)
        assert len(final_chunks) == 3, "expected the 63s marked audio to split into 3 chunks"
        final_starts = np.cumsum([0] + [len(c) for c in final_chunks])[:-1] / SR
        final_ends = np.cumsum([len(c) for c in final_chunks]) / SR
        snapshot_chunks = split_audio_on_silence(snapshot_audio, SR, target_s=25.0, max_s=29.0)
        assert len(snapshot_chunks) == 1, "25s buffer must split into ONE chunk"
        snapshot_starts = np.cumsum([0] + [len(c) for c in snapshot_chunks])[:-1] / SR
        snapshot_ends = np.cumsum([len(c) for c in snapshot_chunks]) / SR

        length_map = _interval_map(
            list(final_chunks) + list(snapshot_chunks),
            np.concatenate([final_starts, snapshot_starts]),
            np.concatenate([final_ends, snapshot_ends]),
        )

        def marker_mock(chunk, sr, prompt=None):
            start, end = length_map[round(len(chunk) / sr, 3)]
            return f"[{start:.2f}-{end:.2f}]"

        # ── streaming phase: snapshot at 25s while recording ──
        tr.is_recording = True
        tr.audio_data = [snapshot_audio]
        tr.streaming_ordered = {}
        tr.streaming_pending = set()
        tr.streaming_partial_path = str(tmp_path / "b4.partial_stream.txt")
        tr.streaming_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="groq-stream"
        )
        tr._groq_chunk_callback = marker_mock
        tr._stream_snapshot_and_submit()
        # stop-like wait: in-flight tasks finish before we snapshot
        tr.streaming_executor.shutdown(wait=True)
        with tr.streaming_lock:
            streamed = dict(tr.streaming_ordered)

        # ── post-stop merge of the FULL recording ──
        tr._groq_chunk_callback = marker_mock
        result = tr._transcribe_with_streaming_merge(full, SR, streamed, None, None)

        assert result is not None
        intervals = _parse_intervals(result)
        # Every final chunk must be transcribed exactly once
        assert len(intervals) == len(final_chunks), (
            f"expected {len(final_chunks)} interval markers, got "
            f"{len(intervals)} in: {result!r}"
        )
        _assert_no_overlap(intervals)

    def test_merge_idempotent_same_checkpoint(self, tmp_path):
        """Invariant: merging the same checkpoint twice must not duplicate.

        The merge output is a pure function of (audio, streamed checkpoint):
        identical inputs produce identical text with no extra markers.
        """
        _reset_circuit()
        tr = _mock_transcriber(tmp_path)
        full = _make_marked_audio(63.0)
        final_chunks = split_audio_on_silence(full, SR, target_s=25.0, max_s=29.0)
        starts = np.cumsum([0] + [len(c) for c in final_chunks])[:-1] / SR
        ends = np.cumsum([len(c) for c in final_chunks]) / SR
        length_map = _interval_map(final_chunks, starts, ends)

        def marker_mock(chunk, sr, prompt=None):
            start, end = length_map[round(len(chunk) / sr, 3)]
            return f"[{start:.2f}-{end:.2f}]"

        tr._groq_chunk_callback = marker_mock
        streamed = {0: "<streamed prefix>"}
        first = tr._transcribe_with_streaming_merge(full, SR, dict(streamed), None, None)
        second = tr._transcribe_with_streaming_merge(full, SR, dict(streamed), None, None)

        assert first is not None
        assert first == second, "same checkpoint must merge to identical text"

    def test_merge_does_not_retranscribe_streamed_indices(self, tmp_path):
        """Invariant: streamed (non-tail) indices are not sent to Groq again."""
        _reset_circuit()
        tr = _mock_transcriber(tmp_path)
        full = _make_marked_audio(63.0)
        final_chunks = split_audio_on_silence(full, SR, target_s=25.0, max_s=29.0)
        total = len(final_chunks)
        starts = np.cumsum([0] + [len(c) for c in final_chunks])[:-1] / SR
        ends = np.cumsum([len(c) for c in final_chunks]) / SR
        length_map = _interval_map(final_chunks, starts, ends)
        calls = {"n": 0}

        def marker_mock(chunk, sr, prompt=None):
            calls["n"] += 1
            start, end = length_map[round(len(chunk) / sr, 3)]
            return f"[{start:.2f}-{end:.2f}]"

        tr._groq_chunk_callback = marker_mock
        streamed = {i: f"<streamed {i}>" for i in range(total - 1)}

        result = tr._transcribe_with_streaming_merge(full, SR, streamed, None, None)

        assert result is not None
        assert "<streamed 0>" in result
        assert calls["n"] == 1, f"merge must only transcribe the tail chunk, called {calls['n']}x"
