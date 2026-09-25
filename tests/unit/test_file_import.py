"""
Unit tests for backend.file_import (F1 Files tab).

Covers the pure import-validation contract:
- is_audio_file: valid / invalid / missing paths
- filter_audio_paths: dedup, mixed batches, per-entry rejection reasons
- split_drop_data: tkinterdnd2 drop-data parsing (braced/plain/quoted paths)
- paths_from_clipboard_text: line splitting, quote stripping, existence filter
- paths_from_clipboard: CF_HDROP preference behind a monkeypatched accessor,
  text fallback (no real clipboard is touched in CI)

Author: Audio2Text Development Team
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend import file_import
from backend.file_import import (
    DEFAULT_AUDIO_EXTENSIONS,
    filter_audio_paths,
    is_audio_file,
    paths_from_clipboard,
    paths_from_clipboard_text,
    split_drop_data,
)


@pytest.mark.unit
class TestIsAudioFile:
    """Tests for the single-path audio validation predicate."""

    def test_valid_audio_file_returns_true(self, tmp_path):
        # Arrange
        audio = tmp_path / "meeting.mp3"
        audio.write_bytes(b"x")

        # Act
        result = is_audio_file(str(audio))

        # Assert
        assert result is True

    def test_invalid_extension_returns_false(self, tmp_path):
        # Arrange
        text_file = tmp_path / "notes.txt"
        text_file.write_text("hello")

        # Act
        result = is_audio_file(str(text_file))

        # Assert
        assert result is False

    def test_extension_match_is_case_insensitive(self, tmp_path):
        # Arrange
        audio = tmp_path / "MEETING.MP3"
        audio.write_bytes(b"x")

        # Act
        result = is_audio_file(str(audio))

        # Assert
        assert result is True

    def test_extensions_with_leading_dot_are_accepted(self, tmp_path):
        # Arrange
        audio = tmp_path / "meeting.wav"
        audio.write_bytes(b"x")

        # Act
        result = is_audio_file(str(audio), frozenset({".wav"}))

        # Assert
        assert result is True

    def test_missing_file_returns_false(self):
        # Arrange
        missing = "Z:/definitely/not/here/talk.mp3"

        # Act
        result = is_audio_file(missing)

        # Assert
        assert result is False

    def test_default_extensions_used_when_none_given(self, tmp_path):
        # Arrange
        webm = tmp_path / "clip.webm"
        webm.write_bytes(b"x")
        txt = tmp_path / "clip.txt"
        txt.write_text("x")

        # Act / Assert
        assert is_audio_file(str(webm)) is True
        assert is_audio_file(str(txt)) is False

    def test_empty_path_returns_false(self):
        # Act / Assert
        assert is_audio_file("") is False

    def test_non_string_path_raises_type_error(self):
        # Act / Assert
        with pytest.raises(TypeError):
            is_audio_file(None)  # type: ignore[arg-type]


@pytest.mark.unit
class TestFilterAudioPaths:
    """Tests for batch filtering: acceptance, rejection reasons, dedup."""

    def test_mixed_batch_is_split_with_reasons(self, tmp_path):
        # Arrange
        valid = tmp_path / "a.mp3"
        valid.write_bytes(b"x")
        wrong_type = tmp_path / "b.txt"
        wrong_type.write_text("x")

        # Act
        accepted, rejected = filter_audio_paths(
            [str(valid), str(wrong_type), str(tmp_path / "c.mp3")]
        )

        # Assert
        assert accepted == [str(valid)]
        assert (str(wrong_type), "invalid_type") in rejected
        assert (str(tmp_path / "c.mp3"), "missing") in rejected

    def test_duplicates_within_batch_are_ignored(self, tmp_path):
        # Arrange
        audio = tmp_path / "a.mp3"
        audio.write_bytes(b"x")

        # Act
        accepted, rejected = filter_audio_paths(
            [str(audio), str(audio), str(audio)]
        )

        # Assert
        assert accepted == [str(audio)]
        assert rejected == []

    def test_duplicate_detection_is_case_insensitive(self, tmp_path):
        # Arrange
        audio = tmp_path / "a.mp3"
        audio.write_bytes(b"x")

        # Act
        accepted, _ = filter_audio_paths([str(audio), str(audio).upper()])

        # Assert
        assert accepted == [str(audio)]

    def test_custom_extensions_override_default(self, tmp_path):
        # Arrange
        custom = tmp_path / "raw.xyz"
        custom.write_bytes(b"x")

        # Act
        accepted, rejected = filter_audio_paths(
            [str(custom)], frozenset({"xyz"})
        )

        # Assert
        assert accepted == [str(custom)]

    def test_empty_input_returns_empty_lists(self):
        # Act
        accepted, rejected = filter_audio_paths([])

        # Assert
        assert accepted == []
        assert rejected == []

    def test_quotes_and_whitespace_are_stripped(self, tmp_path):
        # Arrange
        audio = tmp_path / "a.mp3"
        audio.write_bytes(b"x")

        # Act
        accepted, _ = filter_audio_paths([f'  "{audio}"  '])

        # Assert
        assert accepted == [str(audio)]


@pytest.mark.unit
class TestSplitDropData:
    """Tests for tkinterdnd2 event.data parsing."""

    def test_plain_space_separated_paths(self):
        # Act
        result = split_drop_data("C:/a.mp3 C:/b.wav")

        # Assert
        assert result == ["C:/a.mp3", "C:/b.wav"]

    def test_braced_paths_with_spaces_are_kept_intact(self):
        # Act
        result = split_drop_data("{C:/my dir/a.mp3} {C:/other/b.wav}")

        # Assert
        assert result == ["C:/my dir/a.mp3", "C:/other/b.wav"]

    def test_mixed_braced_and_plain_paths(self):
        # Act
        result = split_drop_data("{C:/my dir/a.mp3} C:/b.wav")

        # Assert
        assert result == ["C:/my dir/a.mp3", "C:/b.wav"]

    def test_quoted_paths_are_unquoted(self):
        # Act
        result = split_drop_data('"C:/my dir/a.mp3"')

        # Assert
        assert result == ["C:/my dir/a.mp3"]

    def test_empty_data_returns_empty_list(self):
        # Act / Assert
        assert split_drop_data("") == []


@pytest.mark.unit
class TestPathsFromClipboardText:
    """Tests for text-path extraction (one path per line)."""

    def test_existing_paths_are_kept(self, tmp_path):
        # Arrange
        audio = tmp_path / "a.mp3"
        audio.write_bytes(b"x")

        # Act
        result = paths_from_clipboard_text(str(audio) + "\n")

        # Assert
        assert result == [str(audio)]

    def test_missing_paths_are_dropped(self):
        # Act
        result = paths_from_clipboard_text("Z:/nope/missing.mp3\n")

        # Assert
        assert result == []

    def test_quoted_lines_are_stripped(self, tmp_path):
        # Arrange
        audio = tmp_path / "a.mp3"
        audio.write_bytes(b"x")

        # Act
        result = paths_from_clipboard_text(f'"{audio}"\n')

        # Assert
        assert result == [str(audio)]

    def test_user_home_is_expanded(self, tmp_path, monkeypatch):
        # Arrange
        audio = tmp_path / "a.mp3"
        audio.write_bytes(b"x")
        monkeypatch.setattr(
            file_import.os.path, "expanduser", lambda p: str(audio)
        )

        # Act
        result = paths_from_clipboard_text("~/a.mp3\n")

        # Assert
        assert result == [str(audio)]

    def test_non_path_text_is_ignored(self):
        # Act
        result = paths_from_clipboard_text("just some words\nanother line\n")

        # Assert
        assert result == []

    def test_empty_text_returns_empty_list(self):
        # Act / Assert
        assert paths_from_clipboard_text("") == []


@pytest.mark.unit
class TestPathsFromClipboard:
    """Tests for the clipboard accessor chain: CF_HDROP first, text fallback."""

    def test_hdrop_result_takes_priority_over_text(self, tmp_path, monkeypatch):
        # Arrange
        audio = tmp_path / "a.mp3"
        audio.write_bytes(b"x")
        monkeypatch.setattr(
            file_import, "_read_clipboard_hdrop", lambda: [str(audio)]
        )
        monkeypatch.setattr(
            file_import, "_read_clipboard_text", lambda: "ignored.mp3"
        )

        # Act
        result = paths_from_clipboard()

        # Assert
        assert result == [str(audio)]

    def test_falls_back_to_text_when_hdrop_is_empty(self, tmp_path, monkeypatch):
        # Arrange
        audio = tmp_path / "a.mp3"
        audio.write_bytes(b"x")
        monkeypatch.setattr(file_import, "_read_clipboard_hdrop", lambda: [])
        monkeypatch.setattr(
            file_import, "_read_clipboard_text", lambda: str(audio) + "\n"
        )

        # Act
        result = paths_from_clipboard()

        # Assert
        assert result == [str(audio)]

    def test_returns_empty_list_when_both_sources_empty(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(file_import, "_read_clipboard_hdrop", lambda: [])
        monkeypatch.setattr(file_import, "_read_clipboard_text", lambda: "")

        # Act
        result = paths_from_clipboard()

        # Assert
        assert result == []


@pytest.mark.unit
class TestDefaultAudioExtensions:
    """Tests for the documented default allowlist."""

    def test_default_allowlist_matches_spec(self):
        # Assert
        assert DEFAULT_AUDIO_EXTENSIONS == frozenset(
            {"mp3", "wav", "m4a", "ogg", "flac", "webm", "opus", "aac"}
        )
