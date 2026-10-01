"""
Unit tests para UTF8Validator — FIX v0.15.0 (bugs A, B, C).

Documenta las correcciones:
- Bug A: la cabecera declaraba latin-1 pero el archivo era UTF-8
- Bug B: validate_encoding era tautología (round-trip encode/decode siempre True)
  → NUNCA detectaba mojibake → el texto corrupto pasaba sin corregir
- Bug C: BOM slicing [3:] se comía 3 caracteres REALES del texto

Author: Audio2Text Development Team
Version: 0.15.0
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utf8_validator import UTF8Validator, MOJIBAKE_MAP


@pytest.mark.unit
class TestUTF8ValidatorFixes:
    """Tests de las correcciones UTF-8 de v0.15.0."""

    def setup_method(self):
        self.validator = UTF8Validator()

    def test_bug_b_detecta_mojibake(self):
        """Bug B: 'validate_encoding' debe detectar mojibake REAL (doble-encoding)."""
        # 'á' mal decodificado como latin-1 se ve como 'Ã¡'
        is_valid, problems = self.validator.validate_encoding("CENF es una empresa de tecnologÃ­a")
        assert not is_valid, "Debe detectar mojibake"
        assert any("mojibake" in p for p in problems)

    def test_bug_b_texto_limpio_es_valido(self):
        """Bug B: texto sin mojibake debe ser válido."""
        is_valid, problems = self.validator.validate_encoding("CENF es una empresa de tecnología")
        assert is_valid
        assert problems == []

    def test_bug_b_normalize_corrige_mojibake(self):
        """Bug B: normalize debe corregir el mojibake real."""
        result = self.validator.normalize_spanish_chars("tecnologÃ­a de la informaciÃ³n")
        assert "tecnología" in result
        assert "información" in result

    def test_bug_b_normalize_transcription_corrige(self):
        """Bug B: flujo completo normalize_transcription corrige mojibake."""
        result = self.validator.normalize_transcription(
            "La empresa CENF usa tecnologÃ­a avanzada", normalize=True
        )
        assert "tecnología" in result

    def test_bug_c_bom_solo_un_caracter(self):
        """Bug C: BOM debe quitarse como UN carácter, no 3."""
        # Texto real: 'hola' — si el BOM slicing fuera [3:] se comería 'hol'
        text = "\ufeffhola"
        result = self.validator.clean_encoding_artifacts(text)
        assert result == "hola", f"Bug C: se comieron caracteres reales -> {result!r}"

    def test_bug_c_bom_con_acentos(self):
        """Bug C: BOM + acentos se preservan correctamente."""
        text = "\ufeffÁÉÍÓÚ"
        result = self.validator.clean_encoding_artifacts(text)
        assert result == "ÁÉÍÓÚ"

    def test_bug_a_encoding_declaration(self):
        """Bug A: el archivo debe declarar utf-8 (no latin-1)."""
        source = Path(__file__).parent.parent / "backend" / "utf8_validator.py"
        first_line = source.read_text(encoding="utf-8").splitlines()[0]
        assert "latin-1" not in first_line, "Bug A: todavía declara latin-1"
        assert "utf-8" in first_line.lower()

    def test_mojibake_map_cubre_acentos_espanol(self):
        """El mapa de mojibake debe cubrir tildes y ñ."""
        for bad, good in MOJIBAKE_MAP.items():
            assert bad != good, f"Entrada inválida en MOJIBAKE_MAP: {bad}"
        assert "Ã¡" in MOJIBAKE_MAP and MOJIBAKE_MAP["Ã¡"] == "á"
        assert "Ã©" in MOJIBAKE_MAP and MOJIBAKE_MAP["Ã©"] == "é"
        assert "Ã±" in MOJIBAKE_MAP and MOJIBAKE_MAP["Ã±"] == "ñ"

    def test_validacion_caracteres_malformados(self):
        """validate_transcription debe marcar caracteres malformados."""
        is_valid, problems = self.validator.validate_transcription("palabra Ã¡ con tilde rota")
        assert not is_valid

    def test_no_destruye_texto_correcto_con_acentos(self):
        """FIX v0.15.0: normalize NO debe tocar texto ya correcto (Brújula, qué, más)."""
        original = "Brújula, ¿qué hacer? Más importante: áéíóúñ"
        result = self.validator.normalize_transcription(original, normalize=True)
        assert result == original, f"Texto correcto fue alterado: {result!r}"

    def test_no_destruye_tilde_simple_literal(self):
        """FIX v0.15.0: una tilde suelta (´) NO debe convertirse en 'á'."""
        # El mapa original MALFORMED_CHARS hacía '´' -> 'á' y '`' -> 'é' (destructivo)
        result = self.validator.normalize_spanish_chars("texto con acento ´ suelto")
        assert "á suelto" not in result, "La tilde suelta se convirtió en 'á'"

    def test_normalize_combina_acentos_nfd_a_nfc(self):
        """FIX v0.15.0: acentos combinados (e + U+0301) se combinan a 'é'."""
        # 'e' + acento agudo combinado (U+0301) = NFD de 'é'
        combined = "e\u0301xito"
        result = self.validator.normalize_spanish_chars(combined)
        assert result == "éxito", f"NFD no combinado: {result!r}"
        assert len(result) == 5  # é-x-i-t-o (5 chars, no 6)
