"""@File: tests/unit/test_vocabulary_service.py
@Description: Unit tests for VocabularyService (Task 3.3a). TDD cycle — RED first.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations


class TestVocabularyServiceInit:
    """Tests for VocabularyService initialization."""

    def test_create_with_default_config(self) -> None:
        """Service can be created with no arguments (uses defaults)."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        assert service is not None


class TestVocabularyServiceApply:
    """Tests for the apply_corrections() method."""

    def test_apply_replaces_known_word(self) -> None:
        """Known words are replaced with their corrections."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        service.add_entry("zenf", "CENF")
        text = "Esto es zenf tecnología"
        result = service.apply_corrections(text)

        assert "CENF" in result
        assert "zenf" not in result

    def test_apply_respects_word_boundaries(self) -> None:
        """Correction only replaces whole words, not substrings."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        service.add_entry("zen", "CENF")
        text = "Es zen, no es zenf ni zenith"
        result = service.apply_corrections(text)

        # "zen" should be replaced, but not "zenf" or "zenith"
        assert "CENF" in result
        assert "zenf" in result  # zenf not replaced (is a different word)
        assert "zenith" in result  # zenith not replaced

    def test_apply_with_no_entries_returns_original(self) -> None:
        """With no entries, text is returned unchanged."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        text = "Hola mundo"
        result = service.apply_corrections(text)

        assert result == text

    def test_apply_handles_empty_text(self) -> None:
        """Empty text returns empty string."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        service.add_entry("test", "fixed")
        assert service.apply_corrections("") == ""

    def test_apply_preserves_case_sensitive(self) -> None:
        """Case is preserved based on matched word."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        service.add_entry("zenf", "CENF")
        # Uppercase match → uppercase replacement
        result = service.apply_corrections("ZENF")
        assert result == "CENF"


class TestVocabularyServiceEntries:
    """Tests for add/remove/toggle entry management."""

    def test_add_entry(self) -> None:
        """add_entry() registers a new correction pair."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        result = service.add_entry("wrong", "correct")
        assert result is True

    def test_add_duplicate_entry_updates(self) -> None:
        """Adding a duplicate key updates the correction."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        service.add_entry("wrong", "correct")
        service.add_entry("wrong", "better")

        result = service.apply_corrections("wrong")
        assert result == "better"

    def test_remove_entry(self) -> None:
        """remove_entry() deletes a correction."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        service.add_entry("wrong", "correct")
        service.remove_entry("wrong")

        result = service.apply_corrections("wrong")
        assert result == "wrong"  # No longer corrected

    def test_remove_nonexistent_entry_returns_false(self) -> None:
        """Removing a nonexistent entry returns False."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        result = service.remove_entry("nonexistent")
        assert result is False

    def test_toggle_entry(self) -> None:
        """toggle_entry() enables/disables entries."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        service.add_entry("wrong", "correct")
        # Toggle off
        service.toggle_entry("wrong", enabled=False)
        result = service.apply_corrections("wrong")
        assert result == "wrong"  # Not corrected when disabled

        # Toggle back on
        service.toggle_entry("wrong", enabled=True)
        result = service.apply_corrections("wrong")
        assert result == "correct"

    def test_get_entries(self) -> None:
        """get_entries() returns all vocabulary entries."""
        from audio2text.services.vocabulary_service import VocabularyService

        service = VocabularyService()
        service.add_entry("a", "A")
        service.add_entry("b", "B")

        entries = service.get_entries()
        assert len(entries) >= 2
        words = [e.word for e in entries]
        assert "a" in words or "A" in words
