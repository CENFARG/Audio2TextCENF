"""Tests for audio2text.services.audio_chunker — client-side audio chunking."""

from __future__ import annotations

import numpy as np
import pytest

from audio2text.services.audio_chunker import (
    CHUNK_THRESHOLD_S,
    DEFAULT_MAX_S,
    DEFAULT_TARGET_S,
    split_audio_on_silence,
    transcribe_chunks,
    _silence_threshold_db,
)


class TestSilenceThreshold:
    """Tests for adaptive silence threshold calculation."""

    def test_high_contrast_audio(self):
        """Audio with clear speech/silence contrast should have higher threshold."""
        db = np.array([-50, -45, -40, -20, -15, -10, -5, -10, -15, -20])
        thr = _silence_threshold_db(db)
        assert thr > -45.0  # Should be above the fallback

    def test_uniform_audio(self):
        """Uniform audio (no clear silences) should fall back to -45 dBFS."""
        db = np.array([-20, -21, -19, -20, -21, -19, -20, -21, -19, -20])
        thr = _silence_threshold_db(db)
        assert thr == -45.0

    def test_threshold_bounds(self):
        """Threshold should always be between -60 and -25 dBFS."""
        for _ in range(100):
            db = np.random.uniform(-60, 0, 100)
            thr = _silence_threshold_db(db)
            assert -60.0 <= thr <= -25.0


class TestSplitAudioOnSilence:
    """Tests for splitting audio on silence boundaries."""

    def test_short_audio_no_split(self):
        """Audio shorter than max_s should not be split."""
        sr = 16000
        audio = np.random.randn(sr * 10).astype(np.float32)  # 10s
        chunks = split_audio_on_silence(audio, sr, max_s=29.0)
        assert len(chunks) == 1
        np.testing.assert_array_equal(chunks[0], audio)

    def test_long_audio_splits(self):
        """Audio longer than max_s should be split into multiple chunks."""
        sr = 16000
        # Create 60s audio with silence at 25s and 50s
        audio = np.random.randn(sr * 60).astype(np.float32)
        # Insert silence at 25s and 50s
        silence_start_1 = int(24.5 * sr)
        silence_end_1 = int(25.5 * sr)
        audio[silence_start_1:silence_end_1] = 0.0

        silence_start_2 = int(49.5 * sr)
        silence_end_2 = int(50.5 * sr)
        audio[silence_start_2:silence_end_2] = 0.0

        chunks = split_audio_on_silence(audio, sr, max_s=29.0)
        assert len(chunks) > 1

    def test_concat_equals_original(self):
        """Concatenation of chunks must equal original audio (invariant 1)."""
        sr = 16000
        audio = np.random.randn(sr * 45).astype(np.float32)
        # Add silence at 25s
        silence_start = int(24.5 * sr)
        silence_end = int(25.5 * sr)
        audio[silence_start:silence_end] = 0.0

        chunks = split_audio_on_silence(audio, sr, max_s=29.0)
        concatenated = np.concatenate(chunks)
        np.testing.assert_array_equal(concatenated, audio)

    def test_no_chunk_exceeds_max(self):
        """No chunk should exceed max_s duration (invariant 2)."""
        sr = 16000
        max_s = 29.0
        audio = np.random.randn(sr * 90).astype(np.float32)
        # Add silences every 25s
        for i in range(1, 4):
            silence_start = int((i * 25 - 0.5) * sr)
            silence_end = int((i * 25 + 0.5) * sr)
            if silence_end < len(audio):
                audio[silence_start:silence_end] = 0.0

        chunks = split_audio_on_silence(audio, sr, max_s=max_s)
        for chunk in chunks:
            assert len(chunk) <= int(max_s * sr) + 1  # Allow 1 sample tolerance

    def test_empty_audio(self):
        """Empty audio should return single empty chunk."""
        sr = 16000
        audio = np.array([], dtype=np.float32)
        chunks = split_audio_on_silence(audio, sr)
        assert len(chunks) == 1
        assert len(chunks[0]) == 0


class TestTranscribeChunks:
    """Tests for transcribing chunked audio."""

    def test_calls_api_for_each_chunk(self):
        """Each chunk should be transcribed via the API call."""
        sr = 16000
        # Create audio that will be split into 2 chunks
        audio = np.random.randn(sr * 50).astype(np.float32)
        # Add silence at 25s
        audio[int(24.5 * sr) : int(25.5 * sr)] = 0.0

        calls = []

        def mock_api(chunk, prompt=None):
            calls.append({"chunk_len": len(chunk), "prompt": prompt})
            return f"Text for chunk {len(calls)}"

        result = transcribe_chunks(audio, sr, api_call=mock_api)
        assert len(calls) == 2
        assert "Text for chunk 1" in result
        assert "Text for chunk 2" in result

    def test_prompt_from_previous_chunk(self):
        """Second chunk should receive prompt from first chunk's text."""
        sr = 16000
        audio = np.random.randn(sr * 50).astype(np.float32)
        audio[int(24.5 * sr) : int(25.5 * sr)] = 0.0

        prompts = []

        def mock_api(chunk, prompt=None):
            prompts.append(prompt)
            return "Hello world test text"

        transcribe_chunks(audio, sr, api_call=mock_api, prompt_chars=100)
        assert prompts[0] is None  # First chunk has no prompt
        assert prompts[1] is not None  # Second chunk has prompt

    def test_overlap_removal(self):
        """Overlapping words between chunks should be removed."""
        sr = 16000
        audio = np.random.randn(sr * 50).astype(np.float32)
        audio[int(24.5 * sr) : int(25.5 * sr)] = 0.0

        call_count = [0]

        def mock_api(chunk, prompt=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return "The quick brown fox"
            else:
                return "fox jumps over the lazy"  # "fox" overlaps

        result = transcribe_chunks(audio, sr, api_call=mock_api)
        # "fox" should appear only once
        assert result.count("fox") == 1

    def test_event_callback(self):
        """Event callback should be called for each chunk."""
        sr = 16000
        audio = np.random.randn(sr * 50).astype(np.float32)
        audio[int(24.5 * sr) : int(25.5 * sr)] = 0.0

        events = []

        def mock_api(chunk, prompt=None):
            return "Test text"

        def on_event(event):
            events.append(event)

        transcribe_chunks(audio, sr, api_call=mock_api, event_callback=on_event)
        assert len(events) == 2
        assert all(e["event_type"] == "chunk_aggregate" for e in events)


class TestConstants:
    """Tests for module constants."""

    def test_chunk_threshold(self):
        """CHUNK_THRESHOLD_S should be slightly below MAX_WINDOW_S."""
        assert CHUNK_THRESHOLD_S < DEFAULT_MAX_S
        assert CHUNK_THRESHOLD_S == 28.0

    def test_max_window(self):
        """DEFAULT_MAX_S should be below Whisper's 30s window."""
        assert DEFAULT_MAX_S <= 30.0
        assert DEFAULT_MAX_S == 29.0
