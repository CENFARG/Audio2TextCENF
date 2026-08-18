"""Tests for audio2text.services.vocabulary_service — import/export functionality."""

from __future__ import annotations

import pytest

from audio2text.services.vocabulary_service import VocabularyService
from audio2text.domain.vocabulary import VocabularyConfig


class TestVocabularyExport:
    """Tests for vocabulary export functionality."""

    def test_export_to_text_equals_format(self):
        """Export should use '=' separator for user-friendly editing."""
        svc = VocabularyService()
        svc.add_entry("hello", "hola")
        svc.add_entry("world", "mundo")
        result = svc.export_to_text()
        assert "hello=hola" in result
        assert "world=mundo" in result

    def test_export_sorted_alphabetically(self):
        """Export should be sorted by word."""
        svc = VocabularyService()
        svc.add_entry("zebra", "cebra")
        svc.add_entry("apple", "manzana")
        result = svc.export_to_text()
        lines = result.strip().split("\n")
        assert lines[0] == "apple=manzana"
        assert lines[1] == "zebra=cebra"

    def test_export_enabled_only(self):
        """Export with enabled_only should skip disabled entries."""
        svc = VocabularyService()
        svc.add_entry("hello", "hola")
        svc.add_entry("world", "mundo")
        svc.toggle_entry("world", enabled=False)
        result = svc.export_to_text(enabled_only=True)
        assert "hello=hola" in result
        assert "world" not in result

    def test_export_empty(self):
        """Export of empty vocabulary should be empty string."""
        svc = VocabularyService()
        result = svc.export_to_text()
        assert result == ""


class TestVocabularyImport:
    """Tests for vocabulary import functionality."""

    def test_import_equals_format(self):
        """Should import 'word=correction' format."""
        svc = VocabularyService()
        count = svc.import_from_text("hello=hola\nworld=mundo")
        assert count == 2
        entries = svc.get_entries()
        assert any(e.word == "hello" and e.correction == "hola" for e in entries)
        assert any(e.word == "world" and e.correction == "mundo" for e in entries)

    def test_import_arrow_format(self):
        """Should import 'word→correction' legacy format."""
        svc = VocabularyService()
        count = svc.import_from_text("hello→hola\nworld→mundo")
        assert count == 2

    def test_import_space_format(self):
        """Should import 'word correction' space-separated format."""
        svc = VocabularyService()
        count = svc.import_from_text("hello hola\nworld mundo")
        assert count == 2

    def test_import_skips_comments(self):
        """Should skip lines starting with '#'."""
        svc = VocabularyService()
        count = svc.import_from_text("# Comment\nhello=hola\n# Another\nworld=mundo")
        assert count == 2

    def test_import_skips_empty_lines(self):
        """Should skip empty lines."""
        svc = VocabularyService()
        count = svc.import_from_text("hello=hola\n\n\nworld=mundo")
        assert count == 2

    def test_import_with_category(self):
        """Should assign category to imported entries."""
        svc = VocabularyService()
        svc.import_from_text("hello=hola", category="spanish")
        entries = svc.get_entries()
        assert entries[0].category == "spanish"

    def test_import_json(self):
        """Should import from JSON-serializable list."""
        svc = VocabularyService()
        entries = [
            {"word": "hello", "correction": "hola"},
            {"word": "world", "correction": "mundo"},
        ]
        count = svc.import_from_json(entries)
        assert count == 2

    def test_export_import_roundtrip(self):
        """Export then import should preserve entries."""
        svc1 = VocabularyService()
        svc1.add_entry("hello", "hola")
        svc1.add_entry("world", "mundo")
        exported = svc1.export_to_text()

        svc2 = VocabularyService()
        svc2.import_from_text(exported)

        entries1 = sorted(svc1.get_entries(), key=lambda e: e.word)
        entries2 = sorted(svc2.get_entries(), key=lambda e: e.word)
        assert len(entries1) == len(entries2)
        for e1, e2 in zip(entries1, entries2):
            assert e1.word == e2.word
            assert e1.correction == e2.correction

    def test_import_json_roundtrip(self):
        """Export to JSON then import should preserve entries."""
        svc1 = VocabularyService()
        svc1.add_entry("hello", "hola")
        exported = svc1.export_to_json()

        svc2 = VocabularyService()
        svc2.import_from_json(exported)

        entries1 = svc1.get_entries()
        entries2 = svc2.get_entries()
        assert len(entries1) == len(entries2)
