"""@File: tests/unit/test_domain_models.py
@Description: Unit tests for Audio2Text domain models (Task 2.2).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import datetime

import numpy as np
import pytest

# ============================================================================
# RED phase — these imports will fail until domain models are implemented.
# ============================================================================


class TestTranscriptionResult:
    """Tests for the TranscriptionResult domain model."""

    def test_create_with_required_fields(self) -> None:
        """TranscriptionResult can be created with text, duration, and language."""
        from audio2text.domain.transcription import TranscriptionResult

        result = TranscriptionResult(
            text="Hola mundo",
            duration_seconds=2.5,
            language="es",
        )
        assert result.text == "Hola mundo"
        assert result.duration_seconds == 2.5
        assert result.language == "es"

    def test_create_with_all_fields(self) -> None:
        """TranscriptionResult accepts all optional fields."""
        from audio2text.domain.transcription import TranscriptionResult

        result = TranscriptionResult(
            text="Hello world",
            duration_seconds=1.0,
            language="en",
            segments=[{"start": 0.0, "end": 1.0, "text": "Hello world"}],
            confidence=0.95,
            provider_name="groq",
            model_name="whisper-large-v3",
        )
        assert result.text == "Hello world"
        assert result.duration_seconds == 1.0
        assert result.language == "en"
        assert len(result.segments) == 1
        assert result.confidence == 0.95
        assert result.provider_name == "groq"
        assert result.model_name == "whisper-large-v3"

    def test_default_values_are_none(self) -> None:
        """Optional fields default to None or empty list."""
        from audio2text.domain.transcription import TranscriptionResult

        result = TranscriptionResult(
            text="test",
            duration_seconds=0.5,
            language="es",
        )
        assert result.segments == []
        assert result.confidence is None
        assert result.provider_name is None
        assert result.model_name is None

    def test_empty_text_is_valid(self) -> None:
        """Empty text is a valid (though undesirable) result."""
        from audio2text.domain.transcription import TranscriptionResult

        result = TranscriptionResult(
            text="",
            duration_seconds=0.0,
            language="es",
        )
        assert result.text == ""

    def test_equality_by_value(self) -> None:
        """Two TranscriptionResults with identical fields are equal."""
        from audio2text.domain.transcription import TranscriptionResult

        r1 = TranscriptionResult(text="a", duration_seconds=1.0, language="es")
        r2 = TranscriptionResult(text="a", duration_seconds=1.0, language="es")
        assert r1 == r2

    def test_inequality_different_text(self) -> None:
        """Two TranscriptionResults with different text are not equal."""
        from audio2text.domain.transcription import TranscriptionResult

        r1 = TranscriptionResult(text="a", duration_seconds=1.0, language="es")
        r2 = TranscriptionResult(text="b", duration_seconds=1.0, language="es")
        assert r1 != r2


class TestTranscriptionConfig:
    """Tests for the TranscriptionConfig domain model."""

    def test_create_with_defaults(self) -> None:
        """TranscriptionConfig creates with sensible defaults."""
        from audio2text.domain.transcription import TranscriptionConfig

        config = TranscriptionConfig()
        assert config.provider_type == "groq"
        assert config.language == "es"
        assert config.model is None
        assert config.device == "auto"
        assert isinstance(config.options, dict)
        assert len(config.options) == 0

    def test_override_provider_type(self) -> None:
        """provider_type can be overridden."""
        from audio2text.domain.transcription import TranscriptionConfig

        config = TranscriptionConfig(provider_type="faster_whisper")
        assert config.provider_type == "faster_whisper"

    def test_override_language(self) -> None:
        """language can be overridden."""
        from audio2text.domain.transcription import TranscriptionConfig

        config = TranscriptionConfig(language="en")
        assert config.language == "en"

    def test_options_dict_is_independent(self) -> None:
        """Modifying the input dict after creation does not affect config."""
        from audio2text.domain.transcription import TranscriptionConfig

        opts = {"beam_size": 5}
        config = TranscriptionConfig(options=opts)
        opts["beam_size"] = 10
        # config.options should still have the original value
        assert config.options["beam_size"] == 5


class TestAudioSegment:
    """Tests for the AudioSegment domain model."""

    def test_create_mono_segment(self) -> None:
        """AudioSegment can hold numpy audio data with metadata."""
        from audio2text.domain.audio import AudioSegment

        data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        seg = AudioSegment(data=data, sample_rate=16000, channels=1)
        assert np.array_equal(seg.data, data)
        assert seg.sample_rate == 16000
        assert seg.channels == 1

    def test_duration_is_computed(self) -> None:
        """AudioSegment.duration is derived from data length and sample_rate."""
        from audio2text.domain.audio import AudioSegment

        sample_rate = 16000
        n_samples = 32000  # exactly 2 seconds
        data = np.zeros(n_samples, dtype=np.float32)
        seg = AudioSegment(data=data, sample_rate=sample_rate, channels=1)
        assert seg.duration == 2.0

    def test_stereo_segment(self) -> None:
        """AudioSegment can hold stereo (2-channel) data."""
        from audio2text.domain.audio import AudioSegment

        data = np.zeros((100, 2), dtype=np.float32)
        seg = AudioSegment(data=data, sample_rate=44100, channels=2)
        assert seg.sample_rate == 44100
        assert seg.channels == 2

    def test_zero_length_segment(self) -> None:
        """Zero-length audio segment has zero duration."""
        from audio2text.domain.audio import AudioSegment

        data = np.array([], dtype=np.float32)
        seg = AudioSegment(data=data, sample_rate=16000, channels=1)
        assert seg.duration == 0.0


class TestAudioFormat:
    """Tests for the AudioFormat enum-like model."""

    def test_wav_format(self) -> None:
        """WAV is a valid audio format."""
        from audio2text.domain.audio import AudioFormat

        assert AudioFormat.WAV.value == "wav"

    def test_mp3_format(self) -> None:
        """MP3 is a valid audio format."""
        from audio2text.domain.audio import AudioFormat

        assert AudioFormat.MP3.value == "mp3"

    def test_flac_format(self) -> None:
        """FLAC is a valid audio format."""
        from audio2text.domain.audio import AudioFormat

        assert AudioFormat.FLAC.value == "flac"

    def test_from_extension_wav(self) -> None:
        """from_extension returns WAV for .wav."""
        from audio2text.domain.audio import AudioFormat

        assert AudioFormat.from_extension("wav") == AudioFormat.WAV

    def test_from_extension_mp3(self) -> None:
        """from_extension returns MP3 for .mp3."""
        from audio2text.domain.audio import AudioFormat

        assert AudioFormat.from_extension("mp3") == AudioFormat.MP3

    def test_from_extension_case_insensitive(self) -> None:
        """from_extension is case-insensitive."""
        from audio2text.domain.audio import AudioFormat

        assert AudioFormat.from_extension("WAV") == AudioFormat.WAV

    def test_from_extension_unknown(self) -> None:
        """from_extension raises ValueError for unknown extensions."""
        from audio2text.domain.audio import AudioFormat

        with pytest.raises(ValueError, match="Unsupported audio format"):
            AudioFormat.from_extension("ogg")

    def test_from_path(self) -> None:
        """from_path extracts extension from a file path."""
        from audio2text.domain.audio import AudioFormat

        assert AudioFormat.from_path("recording.mp3") == AudioFormat.MP3


class TestTranscriptionMetadata:
    """Tests for the TranscriptionMetadata domain model."""

    def test_create_minimal(self) -> None:
        """TranscriptionMetadata can be created with id and filename."""
        from audio2text.domain.metadata import TranscriptionMetadata

        meta = TranscriptionMetadata(
            id="abc123",
            filename="recording_2026-05-12.wav",
        )
        assert meta.id == "abc123"
        assert meta.filename == "recording_2026-05-12.wav"

    def test_create_full(self) -> None:
        """TranscriptionMetadata accepts all optional fields."""
        from audio2text.domain.metadata import TranscriptionMetadata

        now = datetime.datetime(2026, 5, 12, 12, 0, 0)
        meta = TranscriptionMetadata(
            id="abc123",
            filename="rec.wav",
            emoji="🎤",
            title="Reunion semanal",
            tags=["reunion", "proyecto"],
            notes="Transcripcion de prueba",
            created_at=now,
            audio_path="/tmp/rec.wav",
        )
        assert meta.id == "abc123"
        assert meta.emoji == "🎤"
        assert meta.title == "Reunion semanal"
        assert meta.tags == ["reunion", "proyecto"]
        assert meta.notes == "Transcripcion de prueba"
        assert meta.created_at == now
        assert meta.audio_path == "/tmp/rec.wav"

    def test_default_tags_is_empty(self) -> None:
        """If tags not provided, defaults to empty list."""
        from audio2text.domain.metadata import TranscriptionMetadata

        meta = TranscriptionMetadata(id="x", filename="f.wav")
        assert meta.tags == []

    def test_created_at_defaults_to_utcnow(self) -> None:
        """If created_at not provided, defaults to current UTC time."""
        from audio2text.domain.metadata import TranscriptionMetadata

        before = datetime.datetime.now(datetime.timezone.utc)
        meta = TranscriptionMetadata(id="x", filename="f.wav")
        after = datetime.datetime.now(datetime.timezone.utc)
        assert before <= meta.created_at <= after

    def test_equality_by_id(self) -> None:
        """Two metadatas with same id are equal."""
        from audio2text.domain.metadata import TranscriptionMetadata

        m1 = TranscriptionMetadata(id="abc", filename="a.wav")
        m2 = TranscriptionMetadata(id="abc", filename="b.wav")
        assert m1 == m2


class TestVocabularyEntry:
    """Tests for the VocabularyEntry domain model."""

    def test_create_entry(self) -> None:
        """VocabularyEntry holds a word-correction pair."""
        from audio2text.domain.vocabulary import VocabularyEntry

        entry = VocabularyEntry(word="CENF", correction="zenf")
        assert entry.word == "CENF"
        assert entry.correction == "zenf"

    def test_default_category(self) -> None:
        """Default category is 'custom'."""
        from audio2text.domain.vocabulary import VocabularyEntry

        entry = VocabularyEntry(word="test", correction="fixed")
        assert entry.category == "custom"

    def test_default_enabled(self) -> None:
        """VocabularyEntry is enabled by default."""
        from audio2text.domain.vocabulary import VocabularyEntry

        entry = VocabularyEntry(word="test", correction="fixed")
        assert entry.enabled is True

    def test_can_disable(self) -> None:
        """Entry can be explicitly disabled."""
        from audio2text.domain.vocabulary import VocabularyEntry

        entry = VocabularyEntry(word="test", correction="fixed", enabled=False)
        assert entry.enabled is False

    def test_equality_by_word(self) -> None:
        """Two entries with same word are equal."""
        from audio2text.domain.vocabulary import VocabularyEntry

        e1 = VocabularyEntry(word="CENF", correction="zenf")
        e2 = VocabularyEntry(word="CENF", correction="other")
        assert e1 == e2


class TestVocabularyConfig:
    """Tests for the VocabularyConfig domain model."""

    def test_create_empty(self) -> None:
        """VocabularyConfig can be created with no entries."""
        from audio2text.domain.vocabulary import VocabularyConfig

        config = VocabularyConfig()
        assert config.entries == []
        assert config.auto_apply is True

    def test_create_with_entries(self) -> None:
        """VocabularyConfig can hold a list of entries."""
        from audio2text.domain.vocabulary import VocabularyConfig, VocabularyEntry

        e1 = VocabularyEntry(word="CENF", correction="zenf")
        e2 = VocabularyEntry(word="AI", correction="IA", category="tech")
        config = VocabularyConfig(entries=[e1, e2])
        assert len(config.entries) == 2
        assert config.entries[0].word == "CENF"
        assert config.entries[1].word == "AI"

    def test_disable_auto_apply(self) -> None:
        """auto_apply can be set to False."""
        from audio2text.domain.vocabulary import VocabularyConfig

        config = VocabularyConfig(auto_apply=False)
        assert config.auto_apply is False
