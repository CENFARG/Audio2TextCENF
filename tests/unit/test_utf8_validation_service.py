"""@File: tests/unit/test_utf8_validation_service.py
@Description: Unit tests for UTF8ValidationService (Task 3.2). TDD cycle — RED first.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations


class TestUTF8ValidationServiceInit:
    """Tests for UTF8ValidationService creation and defaults."""

    def test_create_with_defaults(self) -> None:
        """Service can be created with no arguments."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        assert service is not None

    def test_create_with_custom_encoding(self) -> None:
        """Service accepts a custom source encoding for mojibake detection."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService(source_encoding="cp1252")
        assert service is not None


class TestUTF8ValidationServiceValidate:
    """Tests for the validate() method."""

    def test_validate_clean_spanish_text(self) -> None:
        """Clean Spanish text validates as valid with no issues."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        result = service.validate("Hola mundo — español con tildes: áéíóúñÁÉÍÓÚÑ")

        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_validate_clean_english_text(self) -> None:
        """Clean English text validates as valid."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        result = service.validate("Hello world! This is a test.")

        assert result.is_valid is True

    def test_validate_detects_mojibake(self) -> None:
        """Text with mojibake (encoding corruption) is flagged as invalid."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        # "señor" corrupted: ñ (U+00F1) → Latin-1 bytes \xc3\xb1 → decoded as UTF-8 = "Ã±"
        corrupted = "seÃ±or"
        result = service.validate(corrupted)

        # Should detect mojibake
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert result.issues_detected > 0

    def test_validate_detects_control_characters(self) -> None:
        """Text with control characters flags issues."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        result = service.validate("texto\x00con\x01nulls")

        assert result.is_valid is False
        assert len(result.issues) > 0


class TestUTF8ValidationServiceCorrect:
    """Tests for the correct() method — fixing encoding issues."""

    def test_correct_fixes_mojibake_single_char(self) -> None:
        """correct() repairs common mojibake: 'Ã±' → 'ñ'."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        # Spanish ñ corrupted: Latin-1 encoded then decoded as UTF-8
        corrupted = "seÃ±or"
        fixed = service.correct(corrupted)

        assert fixed == "señor"

    def test_correct_fixes_mojibake_multiple_chars(self) -> None:
        """correct() fixes multiple mojibake patterns in one text."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        # All Spanish accented chars corrupted
        corrupted = "mÃ¡s o mÃ©nos — Ãºtil y fÃ¡cil"
        fixed = service.correct(corrupted)

        assert fixed == "más o ménos — útil y fácil"

    def test_correct_fixes_uppercase_mojibake(self) -> None:
        """correct() fixes uppercase mojibake: 'Ã\x81' → 'Á'."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        # Á (U+00C1) → Latin-1 bytes 0xC3 0x81 → decoded as UTF-8
        corrupted = "Ã\x81ngel y Ã\x89xito"
        fixed = service.correct(corrupted)

        assert "\x81" not in fixed
        assert "Á" in fixed or "Angel" not in fixed

    def test_correct_preserves_already_clean_text(self) -> None:
        """correct() does not alter clean text."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        clean = "Hola mundo: español con ñ y tildes — áéíóú"
        fixed = service.correct(clean)

        assert fixed == clean

    def test_correct_handles_empty_string(self) -> None:
        """correct() returns empty string for empty input."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        assert service.correct("") == ""

    def test_correct_handles_none_input(self) -> None:
        """correct() returns empty string for None input."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        assert service.correct(None) == ""

    def test_correct_removes_control_characters(self) -> None:
        """correct() strips null bytes and other control chars."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        dirty = "texto\x00con\x01\x02nulls\x07\x08y\x1fmas"
        fixed = service.correct(dirty)

        assert "\x00" not in fixed
        assert "\x01" not in fixed
        assert "\x07" not in fixed

    def test_correct_normalizes_spaces(self) -> None:
        """correct() collapses multiple spaces and strips."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        dirty = "texto    con    muchos     espacios   "
        fixed = service.correct(dirty)

        assert "    " not in fixed
        assert fixed == fixed.strip()


class TestUTF8ValidationServiceNormalize:
    """Tests for the normalize() method — Unicode normalization."""

    def test_normalize_applies_nfc(self) -> None:
        """normalize() applies NFC normalization."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        # NFD form of "cañón" (decomposed)
        decomposed = "can\u0303o\u0301n"  # c-a-ñ-ó-n (NFD)
        normalized = service.normalize(decomposed)

        # Should be in NFC form (composed)
        assert normalized == "cañón"

    def test_normalize_handles_combining_chars(self) -> None:
        """normalize() composes combining characters."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        # "e" + combining acute accent
        text = "cafe\u0301"  # "café" in NFD
        result = service.normalize(text)

        assert result == "café"
        assert len(result) < len(text)

    def test_normalize_idempotent_on_clean_text(self) -> None:
        """normalize() is idempotent — clean text stays clean."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        clean = "Hola mundo: cañón, café, español"
        result = service.normalize(clean)

        assert result == clean

    def test_normalize_handles_empty_string(self) -> None:
        """normalize() returns empty for empty input."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        assert service.normalize("") == ""


class TestUTF8ValidationServiceFullPipeline:
    """Integration tests for the full correct → normalize pipeline."""

    def test_pipeline_correct_then_normalize(self) -> None:
        """correct() followed by normalize() produces clean Spanish text."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        # Corrupted text with mojibake AND decomposed chars
        corrupted = "can\u0303o\u0301n y seÃ±or — mÃ¡s claro"
        fixed = service.correct(corrupted)
        normalized = service.normalize(fixed)

        assert "cañón" in normalized
        assert "señor" in normalized
        assert "más" in normalized

    def test_clean_spanish_passes_unchanged(self) -> None:
        """A complete clean Spanish text passes through unchanged."""
        from audio2text.services.utf8_validation_service import UTF8ValidationService

        service = UTF8ValidationService()
        text = "Hola mundo — Esto es una transcripción en español: cañón, café, útil, fácil, ¿verdad? ¡Claro!"
        result = service.validate(text)

        assert result.is_valid is True
        fixed = service.correct(text)
        assert fixed == text
